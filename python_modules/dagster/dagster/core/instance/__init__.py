import datetime
import logging
import os
import time
from abc import ABCMeta
from collections import defaultdict, namedtuple
from enum import Enum

import six
import yaml
from rx import Observable

from dagster import check, seven
from dagster.config import Field, Permissive
from dagster.core.definitions.pipeline import ExecutionSelector, PipelineDefinition
from dagster.core.errors import (
    DagsterInvalidConfigError,
    DagsterInvariantViolationError,
    DagsterRunAlreadyExists,
    DagsterRunConflict,
)
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.serdes import ConfigurableClass, whitelist_for_serdes
from dagster.seven import get_current_datetime_in_utc
from dagster.utils.merger import merge_dicts
from dagster.utils.yaml_utils import load_yaml_from_globs

from .config import DAGSTER_CONFIG_YAML_FILENAME
from .ref import InstanceRef, compute_logs_directory

# 'airflow_execution_date' and 'is_airflow_ingest_pipeline' are hardcoded tags used in the
# airflow ingestion logic (see: dagster_pipeline_factory.py). 'airflow_execution_date' stores the
# 'execution_date' used in Airflow operator execution and 'is_airflow_ingest_pipeline' determines
# whether 'airflow_execution_date' is needed.
AIRFLOW_EXECUTION_DATE_STR = 'airflow_execution_date'
IS_AIRFLOW_INGEST_PIPELINE_STR = 'is_airflow_ingest_pipeline'


def _is_dagster_home_set():
    return bool(os.getenv('DAGSTER_HOME'))


def _dagster_home():
    dagster_home_path = os.getenv('DAGSTER_HOME')

    if not dagster_home_path:
        raise DagsterInvariantViolationError(
            'DAGSTER_HOME is not set, check is_dagster_home_set before invoking.'
        )

    return os.path.expanduser(dagster_home_path)


def _check_run_equality(pipeline_run, candidate_run):
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
    check.inst_param(candidate_run, 'candidate_run', PipelineRun)

    field_diff = {}
    for field in pipeline_run._fields:
        expected_value = getattr(pipeline_run, field)
        candidate_value = getattr(candidate_run, field)
        if expected_value != candidate_value:
            field_diff[field] = (expected_value, candidate_value)

    return field_diff


def _format_field_diff(field_diff):
    return '\n'.join(
        [
            (
                '    {field_name}:\n'
                + '        Expected: {expected_value}\n'
                + '        Received: {candidate_value}'
            ).format(
                field_name=field_name,
                expected_value=expected_value,
                candidate_value=candidate_value,
            )
            for field_name, (expected_value, candidate_value,) in field_diff.items()
        ]
    )


class _EventListenerLogHandler(logging.Handler):
    def __init__(self, instance):
        self._instance = instance
        super(_EventListenerLogHandler, self).__init__()

    def emit(self, record):
        from dagster.core.events.log import construct_event_record, StructuredLoggerMessage

        try:
            event = construct_event_record(
                StructuredLoggerMessage(
                    name=record.name,
                    message=record.msg,
                    level=record.levelno,
                    meta=record.dagster_meta,
                    record=record,
                )
            )

            self._instance.handle_new_event(event)

        except Exception as e:  # pylint: disable=W0703
            logging.critical('Error during instance event listen')
            logging.exception(str(e))
            raise


class InstanceType(Enum):
    PERSISTENT = 'PERSISTENT'
    EPHEMERAL = 'EPHEMERAL'


class DagsterInstance:
    '''Core abstraction for managing Dagster's access to storage and other resources.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.
    For example, to use Postgres for run and event log storage, you can write a ``dagster.yaml``
    such as the following:

    .. literalinclude:: ../../../../docs/sections/deploying/postgres_dagster.yaml
       :caption: dagster.yaml
       :language: YAML

    Args:
        instance_type (InstanceType): Indicates whether the instance is ephemeral or persistent.
            Users should not attempt to set this value directly or in their ``dagster.yaml`` files.
        local_artifact_storage (LocalArtifactStorage): The local artifact storage is used to
            configure storage for any artifacts that require a local disk, such as schedules, or
            when using the filesystem system storage to manage files and intermediates. By default,
            this will be a :py:class:`dagster.core.storage.root.LocalArtifactStorage`. Configurable
            in ``dagster.yaml`` using the :py:class:`~dagster.serdes.ConfigurableClass`
            machinery.
        run_storage (RunStorage): The run storage is used to store metadata about ongoing and past
            pipeline runs. By default, this will be a
            :py:class:`dagster.core.storage.runs.SqliteRunStorage`. Configurable in ``dagster.yaml``
            using the :py:class:`~dagster.serdes.ConfigurableClass` machinery.
        event_storage (EventLogStorage): Used to store the structured event logs generated by
            pipeline runs. By default, this will be a
            :py:class:`dagster.core.storage.event_log.SqliteEventLogStorage`. Configurable in
            ``dagster.yaml`` using the :py:class:`~dagster.serdes.ConfigurableClass` machinery.
        compute_log_manager (ComputeLogManager): The compute log manager handles stdout and stderr
            logging for solid compute functions. By default, this will be a
            :py:class:`dagster.core.storage.local_compute_log_manager.LocalComputeLogManager`.
            Configurable in ``dagster.yaml`` using the
            :py:class:`~dagster.serdes.ConfigurableClass` machinery.
        run_launcher (Optional[RunLauncher]): Optionally, a run launcher may be used to enable
            a Dagster instance to launch pipeline runs, e.g. on a remote Kubernetes cluster, in
            addition to running them locally.
        dagit_settings (Optional[Dict]): Specifies certain Dagit-specific, per-instance settings,
            such as feature flags. These are set in the ``dagster.yaml`` under the key ``dagit``.
        telemetry_settings (Optional[Dict]): Specifies certain telemetry-specific, per-instance
            settings, such as whether it is enabled. These are set in the ``dagster.yaml`` under
            the key ``telemetry``
        ref (Optional[InstanceRef]): Used by internal machinery to pass instances across process
            boundaries.
    '''

    _PROCESS_TEMPDIR = None

    def __init__(
        self,
        instance_type,
        local_artifact_storage,
        run_storage,
        event_storage,
        compute_log_manager,
        schedule_storage=None,
        scheduler=None,
        run_launcher=None,
        dagit_settings=None,
        telemetry_settings=None,
        ref=None,
    ):
        from dagster.core.storage.compute_log_manager import ComputeLogManager
        from dagster.core.storage.event_log import EventLogStorage
        from dagster.core.storage.root import LocalArtifactStorage
        from dagster.core.storage.runs import RunStorage
        from dagster.core.storage.schedules import ScheduleStorage
        from dagster.core.scheduler import Scheduler
        from dagster.core.launcher import RunLauncher

        self._instance_type = check.inst_param(instance_type, 'instance_type', InstanceType)
        self._local_artifact_storage = check.inst_param(
            local_artifact_storage, 'local_artifact_storage', LocalArtifactStorage
        )
        self._event_storage = check.inst_param(event_storage, 'event_storage', EventLogStorage)
        self._run_storage = check.inst_param(run_storage, 'run_storage', RunStorage)
        self._compute_log_manager = check.inst_param(
            compute_log_manager, 'compute_log_manager', ComputeLogManager
        )
        self._schedule_storage = check.opt_inst_param(
            schedule_storage, 'schedule_storage', ScheduleStorage
        )
        self._scheduler = check.opt_inst_param(scheduler, 'scheduler', Scheduler)
        self._run_launcher = check.opt_inst_param(run_launcher, 'run_launcher', RunLauncher)
        self._dagit_settings = check.opt_dict_param(dagit_settings, 'dagit_settings')
        self._telemetry_settings = check.opt_dict_param(telemetry_settings, 'telemetry_settings')

        self._ref = check.opt_inst_param(ref, 'ref', InstanceRef)

        self._subscribers = defaultdict(list)

    # ctors

    @staticmethod
    def ephemeral(tempdir=None):
        from dagster.core.storage.event_log import InMemoryEventLogStorage
        from dagster.core.storage.root import LocalArtifactStorage
        from dagster.core.storage.runs import InMemoryRunStorage
        from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager

        if tempdir is None:
            tempdir = DagsterInstance.temp_storage()

        return DagsterInstance(
            InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(tempdir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(compute_logs_directory(tempdir)),
        )

    @staticmethod
    def get(fallback_storage=None):
        # 1. Use $DAGSTER_HOME to determine instance if set.
        if _is_dagster_home_set():
            return DagsterInstance.from_config(_dagster_home())

        # 2. If that is not set use the fallback storage directory if provided.
        # This allows us to have a nice out of the box dagit experience where runs are persisted
        # across restarts in a tempdir that gets cleaned up when the dagit watchdog process exits.
        elif fallback_storage is not None:
            return DagsterInstance.from_config(fallback_storage)

        # 3. If all else fails create an ephemeral in memory instance.
        else:
            return DagsterInstance.ephemeral(fallback_storage)

    @staticmethod
    def local_temp(tempdir=None, overrides=None):
        if tempdir is None:
            tempdir = DagsterInstance.temp_storage()

        return DagsterInstance.from_ref(InstanceRef.from_dir(tempdir, overrides=overrides))

    @staticmethod
    def from_config(config_dir, config_filename=DAGSTER_CONFIG_YAML_FILENAME):
        instance_ref = InstanceRef.from_dir(config_dir, config_filename=config_filename)
        return DagsterInstance.from_ref(instance_ref)

    @staticmethod
    def from_ref(instance_ref):
        check.inst_param(instance_ref, 'instance_ref', InstanceRef)
        return DagsterInstance(
            instance_type=InstanceType.PERSISTENT,
            local_artifact_storage=instance_ref.local_artifact_storage,
            run_storage=instance_ref.run_storage,
            event_storage=instance_ref.event_storage,
            compute_log_manager=instance_ref.compute_log_manager,
            schedule_storage=instance_ref.schedule_storage,
            scheduler=instance_ref.scheduler,
            run_launcher=instance_ref.run_launcher,
            dagit_settings=instance_ref.dagit_settings,
            telemetry_settings=instance_ref.telemetry_settings,
            ref=instance_ref,
        )

    # flags

    @property
    def is_persistent(self):
        return self._instance_type == InstanceType.PERSISTENT

    @property
    def is_ephemeral(self):
        return self._instance_type == InstanceType.EPHEMERAL

    def get_ref(self):
        if self._ref:
            return self._ref

        check.failed('Can not produce an instance reference for {t}'.format(t=self))

    @property
    def root_directory(self):
        return self._local_artifact_storage.base_dir

    @staticmethod
    def temp_storage():
        if DagsterInstance._PROCESS_TEMPDIR is None:
            DagsterInstance._PROCESS_TEMPDIR = seven.TemporaryDirectory()
        return DagsterInstance._PROCESS_TEMPDIR.name

    def info_str(self):
        def _info(component):
            prefix = '     '
            # ConfigurableClass may not have inst_data if it's a direct instantiation
            # which happens for ephemeral instances
            if isinstance(component, ConfigurableClass) and component.inst_data:
                return component.inst_data.info_str(prefix)
            if type(component) is dict:
                return prefix + yaml.dump(component, default_flow_style=False).replace(
                    '\n', '\n' + prefix
                )
            return '{}{}\n'.format(prefix, component.__class__.__name__)

        dagit_settings = self._dagit_settings if self._dagit_settings else None
        telemetry_settings = self._telemetry_settings if self._telemetry_settings else None

        return (
            'DagsterInstance components:\n\n'
            '  Local Artifacts Storage:\n{artifact}\n'
            '  Run Storage:\n{run}\n'
            '  Event Log Storage:\n{event}\n'
            '  Compute Log Manager:\n{compute}\n'
            '  Schedule Storage:\n{schedule_storage}\n'
            '  Scheduler:\n{scheduler}\n'
            '  Run Launcher:\n{run_launcher}\n'
            '  Dagit:\n{dagit}\n'
            '  Telemetry:\n{telemetry}\n'
            ''.format(
                artifact=_info(self._local_artifact_storage),
                run=_info(self._run_storage),
                event=_info(self._event_storage),
                compute=_info(self._compute_log_manager),
                schedule_storage=_info(self._schedule_storage),
                scheduler=_info(self._scheduler),
                run_launcher=_info(self._run_launcher),
                dagit=_info(dagit_settings),
                telemetry=_info(telemetry_settings),
            )
        )

    # schedule storage

    @property
    def schedule_storage(self):
        return self._schedule_storage

    # schedule storage

    @property
    def scheduler(self):
        return self._scheduler

    # run launcher

    @property
    def run_launcher(self):
        return self._run_launcher

    # compute logs

    @property
    def compute_log_manager(self):
        return self._compute_log_manager

    @property
    def dagit_settings(self):
        if self._dagit_settings:
            return self._dagit_settings
        return {}

    @property
    def telemetry_enabled(self):
        if self.is_ephemeral:
            return False

        dagster_telemetry_enabled_default = True

        if not self._telemetry_settings:
            return dagster_telemetry_enabled_default

        if 'enabled' in self._telemetry_settings:
            return self._telemetry_settings['enabled']
        else:
            return dagster_telemetry_enabled_default

    def upgrade(self, print_fn=lambda _: None):
        print_fn('Updating run storage...')
        self._run_storage.upgrade()

        print_fn('Updating event storage...')
        self._event_storage.upgrade()

    def dispose(self):
        self._run_storage.dispose()
        self._event_storage.dispose()

    # run storage

    def get_run_by_id(self, run_id):
        return self._run_storage.get_run_by_id(run_id)

    def get_pipeline_snapshot(self, snapshot_id):
        return self._run_storage.get_pipeline_snapshot(snapshot_id)

    def has_pipeline_snapshot(self, snapshot_id):
        return self._run_storage.has_pipeline_snapshot(snapshot_id)

    def get_execution_plan_snapshot(self, snapshot_id):
        return self._run_storage.get_execution_plan_snapshot(snapshot_id)

    def get_run_stats(self, run_id):
        return self._event_storage.get_stats_for_run(run_id)

    def get_run_step_stats(self, run_id):
        return self._event_storage.get_step_stats_for_run(run_id)

    def get_run_tags(self):
        return self._run_storage.get_run_tags()

    def create_run_for_pipeline(
        self,
        pipeline,
        execution_plan=None,
        run_id=None,
        environment_dict=None,
        mode=None,
        selector=None,
        step_keys_to_execute=None,
        status=None,
        tags=None,
        root_run_id=None,
        parent_run_id=None,
    ):
        from dagster.core.execution.api import create_execution_plan
        from dagster.core.execution.plan.plan import ExecutionPlan
        from dagster.core.snap.execution_plan_snapshot import snapshot_from_execution_plan

        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        check.opt_inst_param(execution_plan, 'execution_plan', ExecutionPlan)

        if execution_plan is None:
            execution_plan = create_execution_plan(
                pipeline,
                environment_dict=environment_dict,
                mode=mode,
                step_keys_to_execute=step_keys_to_execute,
            )

        return self.get_or_create_run(
            pipeline_name=pipeline.name,
            run_id=run_id,
            environment_dict=environment_dict,
            mode=check.opt_str_param(mode, 'mode', default=pipeline.get_default_mode_name()),
            selector=check.opt_inst_param(
                selector,
                'selector',
                ExecutionSelector,
                default=ExecutionSelector(name=pipeline.name),
            ),
            step_keys_to_execute=step_keys_to_execute,
            status=status,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            pipeline_snapshot=pipeline.get_pipeline_snapshot(),
            execution_plan_snapshot=snapshot_from_execution_plan(
                execution_plan, pipeline.get_pipeline_snapshot_id()
            ),
        )

    def get_or_create_run(
        self,
        pipeline_name=None,
        run_id=None,
        environment_dict=None,
        mode=None,
        selector=None,
        step_keys_to_execute=None,
        status=None,
        tags=None,
        root_run_id=None,
        parent_run_id=None,
        pipeline_snapshot=None,
        execution_plan_snapshot=None,
    ):

        if tags and IS_AIRFLOW_INGEST_PIPELINE_STR in tags:
            if AIRFLOW_EXECUTION_DATE_STR not in tags:
                tags[AIRFLOW_EXECUTION_DATE_STR] = get_current_datetime_in_utc().isoformat()

        pipeline_run = PipelineRun(
            pipeline_name=pipeline_name,
            run_id=run_id,
            environment_dict=environment_dict,
            mode=mode,
            selector=selector,
            step_keys_to_execute=step_keys_to_execute,
            status=status,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
        )

        if pipeline_snapshot is not None:
            from dagster.core.snap.pipeline_snapshot import create_pipeline_snapshot_id

            pipeline_snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)

            if not self._run_storage.has_pipeline_snapshot(pipeline_snapshot_id):
                returned_pipeline_snapshot_id = self._run_storage.add_pipeline_snapshot(
                    pipeline_snapshot
                )

                check.invariant(pipeline_snapshot_id == returned_pipeline_snapshot_id)

            pipeline_run = pipeline_run.with_pipeline_snapshot_id(pipeline_snapshot_id)

        if execution_plan_snapshot is not None:
            from dagster.core.snap.execution_plan_snapshot import create_execution_plan_snapshot_id

            check.invariant(execution_plan_snapshot.pipeline_snapshot_id == pipeline_snapshot_id)

            execution_plan_snapshot_id = create_execution_plan_snapshot_id(execution_plan_snapshot)

            if not self._run_storage.has_execution_plan_snapshot(execution_plan_snapshot_id):
                returned_execution_plan_snapshot_id = self._run_storage.add_execution_plan_snapshot(
                    execution_plan_snapshot
                )

                check.invariant(execution_plan_snapshot_id == returned_execution_plan_snapshot_id)

            pipeline_run = pipeline_run.with_execution_plan_snapshot_id(execution_plan_snapshot_id)

        if self.has_run(pipeline_run.run_id):
            candidate_run = self.get_run_by_id(pipeline_run.run_id)

            field_diff = _check_run_equality(pipeline_run, candidate_run)

            if field_diff:
                raise DagsterRunConflict(
                    'Found conflicting existing run with same id {run_id}. Runs differ in:'
                    '\n{field_diff}'.format(
                        run_id=pipeline_run.run_id, field_diff=_format_field_diff(field_diff),
                    ),
                )
            return candidate_run

        return self._run_storage.add_run(pipeline_run)

    def add_run(self, pipeline_run):
        return self._run_storage.add_run(pipeline_run)

    def handle_run_event(self, run_id, event):
        return self._run_storage.handle_run_event(run_id, event)

    def has_run(self, run_id):
        return self._run_storage.has_run(run_id)

    def get_runs(self, filters=None, cursor=None, limit=None):
        return self._run_storage.get_runs(filters, cursor, limit)

    def get_runs_count(self, filters=None):
        return self._run_storage.get_runs_count(filters)

    def wipe(self):
        self._run_storage.wipe()
        self._event_storage.wipe()

    def delete_run(self, run_id):
        self._run_storage.delete_run(run_id)
        self._event_storage.delete_events(run_id)

    # event storage

    def logs_after(self, run_id, cursor):
        return self._event_storage.get_logs_for_run(run_id, cursor=cursor)

    def all_logs(self, run_id):
        return self._event_storage.get_logs_for_run(run_id)

    def watch_event_logs(self, run_id, cursor, cb):
        return self._event_storage.watch(run_id, cursor, cb)

    # event subscriptions

    def get_logger(self):
        logger = logging.Logger('__event_listener')
        logger.addHandler(_EventListenerLogHandler(self))
        logger.setLevel(10)
        return logger

    def handle_new_event(self, event):
        run_id = event.run_id

        self._event_storage.store_event(event)

        if event.is_dagster_event and event.dagster_event.is_pipeline_event:
            self._run_storage.handle_run_event(run_id, event.dagster_event)

        for sub in self._subscribers[run_id]:
            sub(event)

    def add_event_listener(self, run_id, cb):
        self._subscribers[run_id].append(cb)

    def report_engine_event(
        self, message, pipeline_run, engine_event_data=None, cls=None, step_key=None,
    ):
        '''
        Report a EngineEvent that occurred outside of a pipeline execution context.
        '''
        from dagster.core.events import EngineEventData, DagsterEvent, DagsterEventType
        from dagster.core.events.log import DagsterEventRecord

        check.class_param(cls, 'cls')
        check.str_param(message, 'message')
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        engine_event_data = check.opt_inst_param(
            engine_event_data, 'engine_event_data', EngineEventData, EngineEventData([]),
        )

        if cls:
            message = "[{}] {}".format(cls.__name__, message)

        log_level = logging.INFO
        if engine_event_data and engine_event_data.error:
            log_level = logging.ERROR

        dagster_event = DagsterEvent(
            event_type_value=DagsterEventType.ENGINE_EVENT.value,
            pipeline_name=pipeline_run.pipeline_name,
            message=message,
            event_specific_data=engine_event_data,
        )
        event_record = DagsterEventRecord(
            message=message,
            user_message=message,
            level=log_level,
            pipeline_name=pipeline_run.pipeline_name,
            run_id=pipeline_run.run_id,
            error_info=None,
            timestamp=time.time(),
            step_key=step_key,
            dagster_event=dagster_event,
        )

        self.handle_new_event(event_record)
        return dagster_event

    def report_run_failed(self, pipeline_run):
        from dagster.core.events import DagsterEvent, DagsterEventType
        from dagster.core.events.log import DagsterEventRecord

        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        message = "This pipeline run has been marked as failed from outside the execution context"

        event_record = DagsterEventRecord(
            message=message,
            user_message=message,
            level=logging.ERROR,
            pipeline_name=pipeline_run.pipeline_name,
            run_id=pipeline_run.run_id,
            error_info=None,
            timestamp=time.time(),
            dagster_event=DagsterEvent(
                event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
                pipeline_name=pipeline_run.pipeline_name,
                message=message,
            ),
        )
        self.handle_new_event(event_record)

    # directories

    def file_manager_directory(self, run_id):
        return self._local_artifact_storage.file_manager_dir(run_id)

    def intermediates_directory(self, run_id):
        return self._local_artifact_storage.intermediates_dir(run_id)

    def schedules_directory(self):
        return self._local_artifact_storage.schedules_dir

    # Run launcher

    def launch_run(self, run):
        return self._run_launcher.launch_run(self, run)

    # Scheduler

    def start_schedule(self, repository, schedule_name):
        return self._scheduler.start_schedule(self, repository, schedule_name)

    def stop_schedule(self, repository, schedule_name):
        return self._scheduler.stop_schedule(self, repository, schedule_name)

    def end_schedule(self, repository, schedule_name):
        return self._scheduler.end_schedule(self, repository, schedule_name)

    # Schedule Storage

    def create_schedule_tick(self, repository, schedule_tick_data):
        return self._schedule_storage.create_schedule_tick(repository, schedule_tick_data)

    def update_schedule_tick(self, repository, tick):
        return self._schedule_storage.update_schedule_tick(repository, tick)

    def get_schedule_ticks_by_schedule(self, repository, schedule_name):
        return self._schedule_storage.get_schedule_ticks_by_schedule(repository, schedule_name)

    def get_schedule_tick_stats_by_schedule(self, repository, schedule_name):
        return self._schedule_storage.get_schedule_tick_stats_by_schedule(repository, schedule_name)

    def all_schedules(self, repository):
        return self._schedule_storage.all_schedules(repository)

    def get_schedule_by_name(self, repository, schedule_name):
        return self._schedule_storage.get_schedule_by_name(repository, schedule_name)

    def add_schedule(self, repository, schedule):
        return self._schedule_storage.add_schedule(repository, schedule)

    def update_schedule(self, repository, schedule):
        return self._schedule_storage.update_schedule(repository, schedule)

    def delete_schedule(self, repository, schedule):
        return self._schedule_storage.delete_schedule(repository, schedule)

    def wipe_all_schedules(self):
        if self._scheduler:
            self._scheduler.wipe(self)

        self._schedule_storage.wipe()

    def log_path_for_schedule(self, repository, schedule_name):
        return self._scheduler.get_log_path(self, repository, schedule_name)
