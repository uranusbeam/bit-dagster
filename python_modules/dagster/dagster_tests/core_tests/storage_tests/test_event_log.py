import multiprocessing
import os
import sys
import time
import traceback
from contextlib import contextmanager

import pytest
import sqlalchemy

from dagster import seven
from dagster.core.definitions import ExpectationResult, Materialization
from dagster.core.errors import DagsterEventLogInvalidForRun
from dagster.core.events import (
    DagsterEvent,
    DagsterEventType,
    EngineEventData,
    StepExpectationResultData,
    StepMaterializationData,
)
from dagster.core.events.log import DagsterEventRecord
from dagster.core.execution.plan.objects import StepFailureData, StepSuccessData
from dagster.core.storage.event_log import (
    InMemoryEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlEventLogStorageTable,
    SqliteEventLogStorage,
)
from dagster.core.storage.sql import create_engine


@contextmanager
def create_in_memory_event_log_storage():
    yield InMemoryEventLogStorage()


@contextmanager
def create_sqlite_run_event_logstorage():
    with seven.TemporaryDirectory() as tmpdir_path:
        yield SqliteEventLogStorage(tmpdir_path)


event_storage_test = pytest.mark.parametrize(
    'event_storage_factory_cm_fn',
    [create_in_memory_event_log_storage, create_sqlite_run_event_logstorage],
)


@event_storage_test
def test_init_log_storage(event_storage_factory_cm_fn):
    with event_storage_factory_cm_fn() as storage:
        if isinstance(storage, InMemoryEventLogStorage):
            assert not storage.is_persistent
        elif isinstance(storage, SqliteEventLogStorage):
            assert storage.is_persistent
        else:
            raise Exception("Invalid event storage type")


@event_storage_test
def test_log_storage_run_not_found(event_storage_factory_cm_fn):
    with event_storage_factory_cm_fn() as storage:
        assert storage.get_logs_for_run('bar') == []


@event_storage_test
def test_event_log_storage_store_events_and_wipe(event_storage_factory_cm_fn):
    with event_storage_factory_cm_fn() as storage:
        assert len(storage.get_logs_for_run('foo')) == 0
        storage.store_event(
            DagsterEventRecord(
                None,
                'Message2',
                'debug',
                '',
                'foo',
                time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ENGINE_EVENT.value,
                    'nonce',
                    event_specific_data=EngineEventData.in_process(999),
                ),
            )
        )
        assert len(storage.get_logs_for_run('foo')) == 1
        assert storage.get_stats_for_run('foo')
        storage.wipe()
        assert len(storage.get_logs_for_run('foo')) == 0


@event_storage_test
def test_event_log_storage_store_with_multiple_runs(event_storage_factory_cm_fn):
    with event_storage_factory_cm_fn() as storage:
        runs = ['foo', 'bar', 'baz']
        for run_id in runs:
            assert len(storage.get_logs_for_run(run_id)) == 0
            storage.store_event(
                DagsterEventRecord(
                    None,
                    'Message2',
                    'debug',
                    '',
                    run_id,
                    time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.STEP_SUCCESS.value,
                        'nonce',
                        event_specific_data=StepSuccessData(duration_ms=100.0),
                    ),
                )
            )

        for run_id in runs:
            assert len(storage.get_logs_for_run(run_id)) == 1
            assert storage.get_stats_for_run(run_id).steps_succeeded == 1

        storage.wipe()
        for run_id in runs:
            assert len(storage.get_logs_for_run(run_id)) == 0


@event_storage_test
def test_event_log_storage_watch(event_storage_factory_cm_fn):
    def evt(name):
        return DagsterEventRecord(
            None,
            name,
            'debug',
            '',
            'foo',
            time.time(),
            dagster_event=DagsterEvent(
                DagsterEventType.ENGINE_EVENT.value,
                'nonce',
                event_specific_data=EngineEventData.in_process(999),
            ),
        )

    with event_storage_factory_cm_fn() as storage:
        watched = []
        watcher = lambda x: watched.append(x)  # pylint: disable=unnecessary-lambda

        assert len(storage.get_logs_for_run('foo')) == 0

        storage.store_event(evt('Message1'))
        assert len(storage.get_logs_for_run('foo')) == 1
        assert len(watched) == 0

        storage.watch('foo', 0, watcher)

        storage.store_event(evt('Message2'))
        storage.store_event(evt('Message3'))
        storage.store_event(evt('Message4'))

        attempts = 10
        while len(watched) < 3 and attempts > 0:
            time.sleep(0.1)
            attempts -= 1

        storage.end_watch('foo', watcher)
        time.sleep(0.3)  # this value scientifically selected from a range of attractive values
        storage.store_event(evt('Message5'))

        assert len(storage.get_logs_for_run('foo')) == 5
        assert len(watched) == 3

        storage.delete_events('foo')

        assert len(storage.get_logs_for_run('foo')) == 0
        assert len(watched) == 3


@event_storage_test
def test_event_log_storage_pagination(event_storage_factory_cm_fn):
    def evt(name):
        return DagsterEventRecord(
            None,
            name,
            'debug',
            '',
            'foo',
            time.time(),
            dagster_event=DagsterEvent(
                DagsterEventType.ENGINE_EVENT.value,
                'nonce',
                event_specific_data=EngineEventData.in_process(999),
            ),
        )

    with event_storage_factory_cm_fn() as storage:
        storage.store_event(evt('Message_0'))
        storage.store_event(evt('Message_1'))
        storage.store_event(evt('Message_2'))

        assert len(storage.get_logs_for_run('foo')) == 3
        assert len(storage.get_logs_for_run('foo', -1)) == 3
        assert len(storage.get_logs_for_run('foo', 0)) == 2
        assert len(storage.get_logs_for_run('foo', 1)) == 1
        assert len(storage.get_logs_for_run('foo', 2)) == 0


@event_storage_test
def test_event_log_delete(event_storage_factory_cm_fn):
    with event_storage_factory_cm_fn() as storage:
        assert len(storage.get_logs_for_run('foo')) == 0
        storage.store_event(
            DagsterEventRecord(
                None,
                'Message2',
                'debug',
                '',
                'foo',
                time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ENGINE_EVENT.value,
                    'nonce',
                    event_specific_data=EngineEventData.in_process(999),
                ),
            )
        )
        assert len(storage.get_logs_for_run('foo')) == 1
        assert storage.get_stats_for_run('foo')
        storage.delete_events('foo')
        assert len(storage.get_logs_for_run('foo')) == 0


@event_storage_test
def test_event_log_get_stats_without_start_and_success(event_storage_factory_cm_fn):
    # When an event log doesn't have a PIPELINE_START or PIPELINE_SUCCESS | PIPELINE_FAILURE event,
    # we want to ensure storage.get_stats_for_run(...) doesn't throw an error.

    with event_storage_factory_cm_fn() as storage:
        assert len(storage.get_logs_for_run('foo')) == 0
        assert storage.get_stats_for_run('foo')


def test_filesystem_event_log_storage_run_corrupted():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)
        # URL begins sqlite:///
        # pylint: disable=protected-access
        with open(os.path.abspath(storage.conn_string_for_run_id('foo')[10:]), 'w') as fd:
            fd.write('some nonsense')
        with pytest.raises(sqlalchemy.exc.DatabaseError):
            storage.get_logs_for_run('foo')


def test_filesystem_event_log_storage_run_corrupted_bad_data():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)
        SqlEventLogStorageMetadata.create_all(create_engine(storage.conn_string_for_run_id('foo')))
        with storage.connect('foo') as conn:
            event_insert = SqlEventLogStorageTable.insert().values(  # pylint: disable=no-value-for-parameter
                run_id='foo', event='{bar}', dagster_event_type=None, timestamp=None
            )
            conn.execute(event_insert)

        with pytest.raises(DagsterEventLogInvalidForRun):
            storage.get_logs_for_run('foo')

        SqlEventLogStorageMetadata.create_all(create_engine(storage.conn_string_for_run_id('bar')))

        with storage.connect('bar') as conn:  # pylint: disable=protected-access
            event_insert = SqlEventLogStorageTable.insert().values(  # pylint: disable=no-value-for-parameter
                run_id='bar', event='3', dagster_event_type=None, timestamp=None
            )
            conn.execute(event_insert)
        with pytest.raises(DagsterEventLogInvalidForRun):
            storage.get_logs_for_run('bar')


def cmd(exceptions, tmpdir_path):
    storage = SqliteEventLogStorage(tmpdir_path)
    try:
        with storage.connect('foo'):
            pass
    except Exception as exc:  # pylint: disable=broad-except
        exceptions.put(exc)
        exc_info = sys.exc_info()
        traceback.print_tb(exc_info[2])


def test_concurrent_sqlite_event_log_connections():
    exceptions = multiprocessing.Queue()

    with seven.TemporaryDirectory() as tmpdir_path:
        ps = []
        for _ in range(5):
            ps.append(multiprocessing.Process(target=cmd, args=(exceptions, tmpdir_path)))
        for p in ps:
            p.start()

        j = 0
        for p in ps:
            p.join()
            j += 1

        assert j == 5

        excs = []
        while not exceptions.empty():
            excs.append(exceptions.get())
        assert not excs, excs


@event_storage_test
def test_event_log_step_stats(event_storage_factory_cm_fn):
    # When an event log doesn't have a PIPELINE_START or PIPELINE_SUCCESS | PIPELINE_FAILURE event,
    # we want to ensure storage.get_stats_for_run(...) doesn't throw an error.

    run_id = 'foo'
    with event_storage_factory_cm_fn() as storage:
        for record in _stats_records(run_id=run_id):
            storage.store_event(record)

        step_stats = storage.get_step_stats_for_run(run_id)
        assert len(step_stats) == 4

        a_stats = [stats for stats in step_stats if stats.step_key == 'A'][0]
        assert a_stats.step_key == 'A'
        assert a_stats.status.value == 'SUCCESS'
        assert a_stats.end_time - a_stats.start_time == 100

        b_stats = [stats for stats in step_stats if stats.step_key == 'B'][0]
        assert b_stats.step_key == 'B'
        assert b_stats.status.value == 'FAILURE'
        assert b_stats.end_time - b_stats.start_time == 50

        c_stats = [stats for stats in step_stats if stats.step_key == 'C'][0]
        assert c_stats.step_key == 'C'
        assert c_stats.status.value == 'SKIPPED'
        assert c_stats.end_time - c_stats.start_time == 25

        d_stats = [stats for stats in step_stats if stats.step_key == 'D'][0]
        assert d_stats.step_key == 'D'
        assert d_stats.status.value == 'SUCCESS'
        assert d_stats.end_time - d_stats.start_time == 150
        assert len(d_stats.materializations) == 3
        assert len(d_stats.expectation_results) == 2


def _stats_records(run_id):
    now = time.time()
    return [
        _event_record(run_id, 'A', now - 325, DagsterEventType.STEP_START),
        _event_record(
            run_id,
            'A',
            now - 225,
            DagsterEventType.STEP_SUCCESS,
            StepSuccessData(duration_ms=100000.0),
        ),
        _event_record(run_id, 'B', now - 225, DagsterEventType.STEP_START),
        _event_record(
            run_id,
            'B',
            now - 175,
            DagsterEventType.STEP_FAILURE,
            StepFailureData(error=None, user_failure_data=None),
        ),
        _event_record(run_id, 'C', now - 175, DagsterEventType.STEP_START),
        _event_record(run_id, 'C', now - 150, DagsterEventType.STEP_SKIPPED),
        _event_record(run_id, 'D', now - 150, DagsterEventType.STEP_START),
        _event_record(
            run_id,
            'D',
            now - 125,
            DagsterEventType.STEP_MATERIALIZATION,
            StepMaterializationData(Materialization(label='mat 1')),
        ),
        _event_record(
            run_id,
            'D',
            now - 100,
            DagsterEventType.STEP_EXPECTATION_RESULT,
            StepExpectationResultData(ExpectationResult(success=True, label='exp 1')),
        ),
        _event_record(
            run_id,
            'D',
            now - 75,
            DagsterEventType.STEP_MATERIALIZATION,
            StepMaterializationData(Materialization(label='mat 2')),
        ),
        _event_record(
            run_id,
            'D',
            now - 50,
            DagsterEventType.STEP_EXPECTATION_RESULT,
            StepExpectationResultData(ExpectationResult(success=False, label='exp 2')),
        ),
        _event_record(
            run_id,
            'D',
            now - 25,
            DagsterEventType.STEP_MATERIALIZATION,
            StepMaterializationData(Materialization(label='mat 3')),
        ),
        _event_record(
            run_id, 'D', now, DagsterEventType.STEP_SUCCESS, StepSuccessData(duration_ms=150000.0)
        ),
    ]


def _event_record(run_id, step_key, timestamp, event_type, event_specific_data=None):
    pipeline_name = 'pipeline_name'
    return DagsterEventRecord(
        None,
        '',
        'debug',
        '',
        run_id,
        timestamp,
        step_key=step_key,
        pipeline_name=pipeline_name,
        dagster_event=DagsterEvent(
            event_type.value,
            pipeline_name,
            step_key=step_key,
            event_specific_data=event_specific_data,
        ),
    )
