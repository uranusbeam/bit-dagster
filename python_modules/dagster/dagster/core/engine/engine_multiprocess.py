import os

from dagster import EventMetadataEntry, check
from dagster.core.errors import DagsterSubprocessError
from dagster.core.events import DagsterEvent, EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_plan_iterator
from dagster.core.execution.config import MultiprocessExecutorConfig
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.instance import DagsterInstance
from dagster.utils import get_multiprocessing_context, start_termination_thread
from dagster.utils.timing import format_duration, time_execution_scope

from .child_process_executor import (
    ChildProcessCommand,
    ChildProcessEvent,
    ChildProcessSystemErrorEvent,
    execute_child_process_command,
)
from .engine_base import Engine

DELEGATE_MARKER = 'multiprocess_subprocess_init'


class InProcessExecutorChildProcessCommand(ChildProcessCommand):
    def __init__(
        self, environment_dict, pipeline_run, executor_config, step_key, instance_ref, term_event
    ):
        self.environment_dict = environment_dict
        self.executor_config = executor_config
        self.pipeline_run = pipeline_run
        self.step_key = step_key
        self.instance_ref = instance_ref
        self.term_event = term_event

    def execute(self):
        check.inst(self.executor_config, MultiprocessExecutorConfig)
        pipeline_def = self.executor_config.load_pipeline(self.pipeline_run)
        instance = DagsterInstance.from_ref(self.instance_ref)

        start_termination_thread(self.term_event)

        execution_plan = create_execution_plan(
            pipeline=pipeline_def,
            environment_dict=self.environment_dict,
            mode=self.pipeline_run.mode,
            step_keys_to_execute=self.pipeline_run.step_keys_to_execute,
        ).build_subset_plan([self.step_key])

        yield instance.report_engine_event(
            'Executing step {} in subprocess'.format(self.step_key),
            self.pipeline_run,
            EngineEventData(
                [
                    EventMetadataEntry.text(str(os.getpid()), 'pid'),
                    EventMetadataEntry.text(self.step_key, 'step_key'),
                ],
                marker_end=DELEGATE_MARKER,
            ),
            MultiprocessEngine,
            self.step_key,
        )

        for step_event in execute_plan_iterator(
            execution_plan,
            self.pipeline_run,
            environment_dict=self.environment_dict,
            retries=self.executor_config.retries.for_inner_plan(),
            instance=instance,
        ):
            yield step_event


def execute_step_out_of_process(step_context, step, errors, term_events):
    command = InProcessExecutorChildProcessCommand(
        step_context.environment_dict,
        step_context.pipeline_run,
        step_context.executor_config,
        step.key,
        step_context.instance.get_ref(),
        term_events[step.key],
    )

    yield DagsterEvent.engine_event(
        step_context,
        'Launching subprocess for {}'.format(step.key),
        EngineEventData(marker_start=DELEGATE_MARKER),
        step_key=step.key,
    )

    for ret in execute_child_process_command(command):
        if ret is None or isinstance(ret, DagsterEvent):
            yield ret
        elif isinstance(ret, ChildProcessEvent):
            if isinstance(ret, ChildProcessSystemErrorEvent):
                errors[ret.pid] = ret.error_info
        elif isinstance(ret, KeyboardInterrupt):
            yield DagsterEvent.engine_event(
                step_context,
                'Multiprocess engine: received KeyboardInterrupt - forwarding to active child processes',
                EngineEventData.interrupted(list(term_events.keys())),
            )
            for term_event in term_events.values():
                term_event.set()
        else:
            check.failed('Unexpected return value from child process {}'.format(type(ret)))


class MultiprocessEngine(Engine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

        intermediates_manager = pipeline_context.intermediates_manager

        limit = pipeline_context.executor_config.max_concurrent

        yield DagsterEvent.engine_event(
            pipeline_context,
            'Executing steps using multiprocess engine: parent process (pid: {pid})'.format(
                pid=os.getpid()
            ),
            event_specific_data=EngineEventData.multiprocess(
                os.getpid(), step_keys_to_execute=execution_plan.step_keys_to_execute
            ),
        )

        # It would be good to implement a reference tracking algorithm here so we could
        # garbage collection results that are no longer needed by any steps
        # https://github.com/dagster-io/dagster/issues/811
        with time_execution_scope() as timer_result:

            active_execution = execution_plan.start(
                retries=pipeline_context.executor_config.retries
            )
            active_iters = {}
            errors = {}
            term_events = {}
            stopping = False

            while (not stopping and not active_execution.is_complete) or active_iters:
                try:
                    # start iterators
                    while len(active_iters) < limit and not stopping:
                        steps = active_execution.get_steps_to_execute(
                            limit=(limit - len(active_iters))
                        )

                        if not steps:
                            break

                        for step in steps:
                            step_context = pipeline_context.for_step(step)
                            term_events[step.key] = get_multiprocessing_context().Event()
                            active_iters[step.key] = execute_step_out_of_process(
                                step_context, step, errors, term_events
                            )

                    # process active iterators
                    empty_iters = []
                    for key, step_iter in active_iters.items():
                        try:
                            event_or_none = next(step_iter)
                            if event_or_none is None:
                                continue
                            else:
                                yield event_or_none
                                active_execution.handle_event(event_or_none)

                        except StopIteration:
                            empty_iters.append(key)

                    # clear and mark complete finished iterators
                    for key in empty_iters:
                        del active_iters[key]
                        if term_events[key].is_set():
                            stopping = True
                        del term_events[key]
                        active_execution.verify_complete(pipeline_context, key)

                    # process skips from failures or uncovered inputs
                    for event in active_execution.skipped_step_events_iterator(pipeline_context):
                        yield event

                # In the very small chance that we get interrupted in this coordination section and not
                # polling the subprocesses for events - try to clean up gracefully
                except KeyboardInterrupt:
                    yield DagsterEvent.engine_event(
                        pipeline_context,
                        'Multiprocess engine: received KeyboardInterrupt - forwarding to active child processes',
                        EngineEventData.interrupted(list(term_events.keys())),
                    )
                    stopping = True
                    for event in term_events.values():
                        event.set()

            errs = {pid: err for pid, err in errors.items() if err}
            if errs:
                raise DagsterSubprocessError(
                    'During multiprocess execution errors occurred in child processes:\n{error_list}'.format(
                        error_list='\n'.join(
                            [
                                'In process {pid}: {err}'.format(pid=pid, err=err.to_string())
                                for pid, err in errs.items()
                            ]
                        )
                    ),
                    subprocess_error_infos=list(errs.values()),
                )

        yield DagsterEvent.engine_event(
            pipeline_context,
            'Multiprocess engine: parent process exiting after {duration} (pid: {pid})'.format(
                duration=format_duration(timer_result.millis), pid=os.getpid()
            ),
            event_specific_data=EngineEventData.multiprocess(os.getpid()),
        )
