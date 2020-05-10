import pytest

from dagster.core.definitions import PipelineDefinition
from dagster.core.errors import DagsterRunAlreadyExists, DagsterSnapshotDoesNotExist
from dagster.core.snap.pipeline_snapshot import create_pipeline_snapshot_id
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.core.utils import make_new_run_id
from dagster.serdes import serialize_pp


class TestRunStorage:
    '''
    You can extend this class to easily run these set of tests on any run storage. When extending,
    you simply need to override the `run_storage` fixture and return your implementation of
    `RunStorage`.

    For example:

    ```
    TestRunStorage.__test__ = False

    class TestMyStorageImplementation(TestRunStorage):
        __test__ = True

        @pytest.fixture(scope='function', name='storage')
        def run_storage(self):  # pylint: disable=arguments-differ
            return MyStorageImplementation()
    ```
    '''

    @pytest.fixture(name='storage', params=[])
    def run_storage(self, request):
        with request.param() as s:
            yield s

    @staticmethod
    def build_run(
        run_id, pipeline_name, mode='default', tags=None, status=PipelineRunStatus.NOT_STARTED
    ):
        from dagster.core.definitions.pipeline import ExecutionSelector

        return PipelineRun(
            pipeline_name=pipeline_name,
            run_id=run_id,
            environment_dict=None,
            mode=mode,
            selector=ExecutionSelector(pipeline_name),
            step_keys_to_execute=None,
            tags=tags,
            status=status,
        )

    def test_basic_storage(self, storage):
        assert storage
        run_id = make_new_run_id()
        added = storage.add_run(
            TestRunStorage.build_run(run_id=run_id, pipeline_name='some_pipeline')
        )
        assert added
        runs = storage.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.run_id == run_id
        assert run.pipeline_name == 'some_pipeline'
        assert storage.has_run(run_id)
        fetched_run = storage.get_run_by_id(run_id)
        assert fetched_run.run_id == run_id
        assert fetched_run.pipeline_name == 'some_pipeline'

    def test_clear(self, storage):
        assert storage
        run_id = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=run_id, pipeline_name='some_pipeline'))
        assert len(storage.get_runs()) == 1
        storage.wipe()
        assert list(storage.get_runs()) == []

    def test_fetch_by_pipeline(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=one, pipeline_name='some_pipeline'))
        storage.add_run(TestRunStorage.build_run(run_id=two, pipeline_name='some_other_pipeline'))
        assert len(storage.get_runs()) == 2
        some_runs = storage.get_runs(PipelineRunsFilter(pipeline_name='some_pipeline'))
        assert len(some_runs) == 1
        assert some_runs[0].run_id == one

    def test_fetch_by_filter(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()

        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                pipeline_name='some_pipeline',
                tags={'tag': 'hello', 'tag2': 'world'},
                status=PipelineRunStatus.SUCCESS,
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                pipeline_name='some_pipeline',
                tags={'tag': 'hello'},
                status=PipelineRunStatus.FAILURE,
            ),
        )

        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, pipeline_name='other_pipeline', status=PipelineRunStatus.SUCCESS
            )
        )

        assert len(storage.get_runs()) == 3

        some_runs = storage.get_runs(PipelineRunsFilter(run_id=one))
        count = storage.get_runs_count(PipelineRunsFilter(run_id=one))
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(pipeline_name='some_pipeline'))
        count = storage.get_runs_count(PipelineRunsFilter(pipeline_name='some_pipeline'))
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(status=PipelineRunStatus.SUCCESS))
        count = storage.get_runs_count(PipelineRunsFilter(status=PipelineRunStatus.SUCCESS))
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == three
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(tags={'tag': 'hello'}))
        count = storage.get_runs_count(PipelineRunsFilter(tags={'tag': 'hello'}))
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(tags={'tag': 'hello', 'tag2': 'world'}))
        count = storage.get_runs_count(PipelineRunsFilter(tags={'tag': 'hello', 'tag2': 'world'}))
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(
            PipelineRunsFilter(pipeline_name="some_pipeline", tags={'tag': 'hello'})
        )
        count = storage.get_runs_count(
            PipelineRunsFilter(pipeline_name="some_pipeline", tags={'tag': 'hello'})
        )
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(
            PipelineRunsFilter(
                pipeline_name="some_pipeline",
                tags={'tag': 'hello'},
                status=PipelineRunStatus.SUCCESS,
            )
        )
        count = storage.get_runs_count(
            PipelineRunsFilter(
                pipeline_name="some_pipeline",
                tags={'tag': 'hello'},
                status=PipelineRunStatus.SUCCESS,
            )
        )
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        # All filters
        some_runs = storage.get_runs(
            PipelineRunsFilter(
                run_id=one,
                pipeline_name="some_pipeline",
                tags={'tag': 'hello'},
                status=PipelineRunStatus.SUCCESS,
            )
        )
        count = storage.get_runs_count(
            PipelineRunsFilter(
                run_id=one,
                pipeline_name="some_pipeline",
                tags={'tag': 'hello'},
                status=PipelineRunStatus.SUCCESS,
            )
        )
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter())
        count = storage.get_runs_count(PipelineRunsFilter())
        assert len(some_runs) == 3
        assert count == 3

    def test_fetch_count_by_tag(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                pipeline_name='some_pipeline',
                tags={'mytag': 'hello', 'mytag2': 'world'},
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                pipeline_name='some_pipeline',
                tags={'mytag': 'goodbye', 'mytag2': 'world'},
            )
        )
        storage.add_run(TestRunStorage.build_run(run_id=three, pipeline_name='some_pipeline'))
        assert len(storage.get_runs()) == 3

        run_count = storage.get_runs_count(
            filters=PipelineRunsFilter(tags={'mytag': 'hello', 'mytag2': 'world'})
        )
        assert run_count == 1

        run_count = storage.get_runs_count(filters=PipelineRunsFilter(tags={'mytag2': 'world'}))
        assert run_count == 2

        run_count = storage.get_runs_count()
        assert run_count == 3

        assert storage.get_run_tags() == [('mytag', {'hello', 'goodbye'}), ('mytag2', {'world'})]

    def test_fetch_by_tags(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                pipeline_name='some_pipeline',
                tags={'mytag': 'hello', 'mytag2': 'world'},
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                pipeline_name='some_pipeline',
                tags={'mytag': 'goodbye', 'mytag2': 'world'},
            )
        )
        storage.add_run(TestRunStorage.build_run(run_id=three, pipeline_name='some_pipeline'))
        assert len(storage.get_runs()) == 3

        some_runs = storage.get_runs(PipelineRunsFilter(tags={'mytag': 'hello', 'mytag2': 'world'}))

        assert len(some_runs) == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(tags={'mytag2': 'world'}))
        assert len(some_runs) == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(tags={}))
        assert len(some_runs) == 3

    def test_paginated_fetch(self, storage):
        assert storage
        one, two, three = [make_new_run_id(), make_new_run_id(), make_new_run_id()]
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, pipeline_name='some_pipeline', tags={'mytag': 'hello'}
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, pipeline_name='some_pipeline', tags={'mytag': 'hello'}
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, pipeline_name='some_pipeline', tags={'mytag': 'hello'}
            )
        )

        all_runs = storage.get_runs()
        assert len(all_runs) == 3
        sliced_runs = storage.get_runs(cursor=three, limit=1)
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two

        all_runs = storage.get_runs(PipelineRunsFilter(pipeline_name='some_pipeline'))
        assert len(all_runs) == 3
        sliced_runs = storage.get_runs(
            PipelineRunsFilter(pipeline_name='some_pipeline'), cursor=three, limit=1
        )
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two

        all_runs = storage.get_runs(PipelineRunsFilter(tags={'mytag': 'hello'}))
        assert len(all_runs) == 3
        sliced_runs = storage.get_runs(
            PipelineRunsFilter(tags={'mytag': 'hello'}), cursor=three, limit=1
        )
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two

    def test_fetch_by_status(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        four = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, pipeline_name='some_pipeline', status=PipelineRunStatus.NOT_STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, pipeline_name='some_pipeline', status=PipelineRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, pipeline_name='some_pipeline', status=PipelineRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=four, pipeline_name='some_pipeline', status=PipelineRunStatus.FAILURE
            )
        )

        assert {
            run.run_id
            for run in storage.get_runs(PipelineRunsFilter(status=PipelineRunStatus.NOT_STARTED))
        } == {one}

        assert {
            run.run_id
            for run in storage.get_runs(PipelineRunsFilter(status=PipelineRunStatus.STARTED))
        } == {two, three,}

        assert {
            run.run_id
            for run in storage.get_runs(PipelineRunsFilter(status=PipelineRunStatus.FAILURE))
        } == {four}

        assert {
            run.run_id
            for run in storage.get_runs(PipelineRunsFilter(status=PipelineRunStatus.SUCCESS))
        } == set()

    def test_fetch_by_status_cursored(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        four = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, pipeline_name='some_pipeline', status=PipelineRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, pipeline_name='some_pipeline', status=PipelineRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, pipeline_name='some_pipeline', status=PipelineRunStatus.NOT_STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=four, pipeline_name='some_pipeline', status=PipelineRunStatus.STARTED
            )
        )

        cursor_four_runs = storage.get_runs(
            PipelineRunsFilter(status=PipelineRunStatus.STARTED), cursor=four
        )
        assert len(cursor_four_runs) == 2
        assert {run.run_id for run in cursor_four_runs} == {one, two}

        cursor_two_runs = storage.get_runs(
            PipelineRunsFilter(status=PipelineRunStatus.STARTED), cursor=two
        )
        assert len(cursor_two_runs) == 1
        assert {run.run_id for run in cursor_two_runs} == {one}

        cursor_one_runs = storage.get_runs(
            PipelineRunsFilter(status=PipelineRunStatus.STARTED), cursor=one
        )
        assert not cursor_one_runs

        cursor_four_limit_one = storage.get_runs(
            PipelineRunsFilter(status=PipelineRunStatus.STARTED), cursor=four, limit=1
        )
        assert len(cursor_four_limit_one) == 1
        assert cursor_four_limit_one[0].run_id == two

    def test_delete(self, storage):
        assert storage
        run_id = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=run_id, pipeline_name='some_pipeline'))
        assert len(storage.get_runs()) == 1
        storage.delete_run(run_id)
        assert list(storage.get_runs()) == []

    def test_delete_with_tags(self, storage):
        assert storage
        run_id = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=run_id, pipeline_name='some_pipeline', tags={run_id: run_id},
            )
        )
        assert len(storage.get_runs()) == 1
        assert run_id in [key for key, value in storage.get_run_tags()]
        storage.delete_run(run_id)
        assert list(storage.get_runs()) == []
        assert run_id not in [key for key, value in storage.get_run_tags()]

    def test_wipe_tags(self, storage):
        run_id = 'some_run_id'
        run = PipelineRun(run_id=run_id, pipeline_name='a_pipeline', tags={'foo': 'bar'})

        storage.add_run(run)

        assert storage.get_run_by_id(run_id) == run
        assert dict(storage.get_run_tags()) == {'foo': {'bar'}}

        storage.wipe()
        assert list(storage.get_runs()) == []
        assert dict(storage.get_run_tags()) == {}

    def test_write_conflicting_run_id(self, storage):
        double_run_id = 'double_run_id'
        pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])

        run = PipelineRun(run_id=double_run_id, pipeline_name=pipeline_def.name)

        assert storage.add_run(run)
        with pytest.raises(DagsterRunAlreadyExists):
            storage.add_run(run)

    def test_add_get_snapshot(self, storage):
        pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])
        pipeline_snapshot = pipeline_def.get_pipeline_snapshot()
        pipeline_snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)

        assert storage.add_pipeline_snapshot(pipeline_snapshot) == pipeline_snapshot_id
        fetched_pipeline_snapshot = storage.get_pipeline_snapshot(pipeline_snapshot_id)
        assert fetched_pipeline_snapshot
        assert serialize_pp(fetched_pipeline_snapshot) == serialize_pp(pipeline_snapshot)
        assert storage.has_pipeline_snapshot(pipeline_snapshot_id)
        assert not storage.has_pipeline_snapshot('nope')

        storage.wipe()

        assert not storage.has_pipeline_snapshot(pipeline_snapshot_id)

    def test_single_write_read_with_snapshot(self, storage):
        run_with_snapshot_id = 'lkasjdflkjasdf'
        pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])

        pipeline_snapshot = pipeline_def.get_pipeline_snapshot()

        pipeline_snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)

        run_with_snapshot = PipelineRun(
            run_id=run_with_snapshot_id,
            pipeline_name=pipeline_def.name,
            pipeline_snapshot_id=pipeline_snapshot_id,
        )

        assert not storage.has_pipeline_snapshot(pipeline_snapshot_id)

        assert storage.add_pipeline_snapshot(pipeline_snapshot) == pipeline_snapshot_id

        assert serialize_pp(storage.get_pipeline_snapshot(pipeline_snapshot_id)) == serialize_pp(
            pipeline_snapshot
        )

        storage.add_run(run_with_snapshot)

        assert storage.get_run_by_id(run_with_snapshot_id) == run_with_snapshot

        storage.wipe()

        assert not storage.has_pipeline_snapshot(pipeline_snapshot_id)
        assert not storage.has_run(run_with_snapshot_id)

    def test_single_write_with_missing_snapshot(self, storage):

        run_with_snapshot_id = 'lkasjdflkjasdf'
        pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])

        run_with_missing_snapshot = PipelineRun(
            run_id=run_with_snapshot_id,
            pipeline_name=pipeline_def.name,
            pipeline_snapshot_id='nope',
        )

        with pytest.raises(DagsterSnapshotDoesNotExist):
            storage.add_run(run_with_missing_snapshot)

    def test_add_get_execution_snapshot(self, storage):
        from dagster.core.execution.api import create_execution_plan
        from dagster.core.snap.execution_plan_snapshot import snapshot_from_execution_plan

        pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])
        execution_plan = create_execution_plan(pipeline_def)
        ep_snapshot = snapshot_from_execution_plan(
            execution_plan, pipeline_def.get_pipeline_snapshot_id()
        )

        snapshot_id = storage.add_execution_plan_snapshot(ep_snapshot)
        fetched_ep_snapshot = storage.get_execution_plan_snapshot(snapshot_id)
        assert fetched_ep_snapshot
        assert serialize_pp(fetched_ep_snapshot) == serialize_pp(ep_snapshot)
        assert storage.has_execution_plan_snapshot(snapshot_id)
        assert not storage.has_execution_plan_snapshot('nope')

        storage.wipe()

        assert not storage.has_execution_plan_snapshot(snapshot_id)
