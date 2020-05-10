from collections import defaultdict

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError, DagsterRunNotFoundError
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.object_store import ObjectStoreOperation, ObjectStoreOperationType


def validate_reexecution_memoization(pipeline_context, execution_plan):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

    parent_run_id = pipeline_context.pipeline_run.parent_run_id
    check.opt_str_param(parent_run_id, 'parent_run_id')

    if parent_run_id is None:
        return

    if not pipeline_context.instance.has_run(parent_run_id):
        raise DagsterRunNotFoundError(
            'Run id {} set as parent run id was not found in instance'.format(parent_run_id),
            invalid_run_id=parent_run_id,
        )

    # exclude full pipeline re-execution
    if len(execution_plan.step_keys_to_execute) == len(execution_plan.steps):
        return

    if not pipeline_context.intermediates_manager.is_persistent:
        raise DagsterInvariantViolationError(
            'Cannot perform reexecution with non persistent intermediates manager `{}`.'.format(
                pipeline_context.intermediates_manager.__class__.__name__
            )
        )


def copy_required_intermediates_for_execution(pipeline_context, execution_plan):
    '''
    Uses the intermediates manager to copy intermediates from the previous run that apply to the
    current execution plan, and yields the corresponding events
    '''
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    parent_run_id = pipeline_context.pipeline_run.parent_run_id

    if not parent_run_id:
        return

    parent_run_logs = pipeline_context.instance.all_logs(parent_run_id)

    output_handles_for_current_run = output_handles_from_execution_plan(execution_plan)
    output_handles_from_previous_run = output_handles_from_event_logs(parent_run_logs)
    output_handles_to_copy = output_handles_for_current_run.intersection(
        output_handles_from_previous_run
    )
    output_handles_to_copy_by_step = defaultdict(list)
    for handle in output_handles_to_copy:
        output_handles_to_copy_by_step[handle.step_key].append(handle)

    intermediates_manager = pipeline_context.intermediates_manager
    for step in execution_plan.topological_steps():
        step_context = pipeline_context.for_step(step)
        for handle in output_handles_to_copy_by_step.get(step.key, []):
            if intermediates_manager.has_intermediate(pipeline_context, handle):
                continue

            operation = intermediates_manager.copy_intermediate_from_run(
                pipeline_context, parent_run_id, handle
            )
            yield DagsterEvent.object_store_operation(
                step_context,
                ObjectStoreOperation.serializable(operation, value_name=handle.output_name),
            )


def is_step_failure_event(record):
    check.inst_param(record, 'record', EventRecord)
    if not record.is_dagster_event:
        return False

    return record.dagster_event.event_type_value == DagsterEventType.STEP_FAILURE.value


def is_intermediate_store_write_event(record):
    check.inst_param(record, 'record', EventRecord)
    if not record.is_dagster_event:
        return False

    write_ops = (
        ObjectStoreOperationType.SET_OBJECT.value,
        ObjectStoreOperationType.CP_OBJECT.value,
    )
    return (
        record.dagster_event.event_type_value == DagsterEventType.OBJECT_STORE_OPERATION.value
        and record.dagster_event.event_specific_data.op in write_ops
    )


def output_handles_from_event_logs(event_logs):
    output_handles_from_previous_run = set()
    failed_step_keys = set(
        record.dagster_event.step_key for record in event_logs if is_step_failure_event(record)
    )

    for record in event_logs:
        if not is_intermediate_store_write_event(record):
            continue

        if record.dagster_event.step_key in failed_step_keys:
            # skip output events from failed steps
            continue

        output_handles_from_previous_run.add(
            StepOutputHandle(
                record.dagster_event.step_key, record.dagster_event.event_specific_data.value_name
            )
        )

    return output_handles_from_previous_run


def output_handles_from_execution_plan(execution_plan):
    output_handles_for_current_run = set()
    for step_level in execution_plan.execution_step_levels():
        for step in step_level:
            for step_input in step.step_inputs:
                if step_input.source_handles:
                    output_handles_for_current_run.update(step_input.source_handles)
    return output_handles_for_current_run


def get_retry_steps_from_execution_plan(instance, execution_plan, parent_run_id):
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.opt_str_param(parent_run_id, 'parent_run_id')

    if not parent_run_id:
        return execution_plan.step_keys_to_execute

    parent_run = instance.get_run_by_id(parent_run_id)
    parent_run_logs = instance.all_logs(parent_run_id)
    steps_in_parent_run_logs = set(
        record.dagster_event.step_key
        for record in parent_run_logs
        if record.dagster_event and record.dagster_event.step_key
    )
    failed_step_keys = set(
        record.dagster_event.step_key for record in parent_run_logs if is_step_failure_event(record)
    )

    to_retry = []

    execution_deps = execution_plan.execution_deps()
    for step in execution_plan.topological_steps():
        if parent_run.step_keys_to_execute and step.key not in parent_run.step_keys_to_execute:
            continue

        if step.key in failed_step_keys:
            to_retry.append(step.key)
            continue

        # include the steps that did not run
        # e.g. when the run was terminated through the dagit "terminate" button
        if step.key not in steps_in_parent_run_logs:
            to_retry.append(step.key)
            continue

        step_deps = execution_deps[step.key]
        if step_deps.intersection(to_retry):
            # this step is downstream of a step we are about to retry
            to_retry.append(step.key)

    return to_retry
