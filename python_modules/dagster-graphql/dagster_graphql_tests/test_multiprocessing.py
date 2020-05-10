import csv
import os
import time
from collections import OrderedDict
from copy import deepcopy

from dagster_graphql.implementation.pipeline_execution_manager import (
    QueueingSubprocessExecutionManager,
    SubprocessExecutionManager,
)

from dagster import (
    ExecutionTargetHandle,
    Field,
    InputDefinition,
    Int,
    Materialization,
    OutputDefinition,
    Path,
    PythonObjectDagsterType,
    String,
    composite_solid,
    input_hydration_config,
    lambda_solid,
    output_materialization_config,
    pipeline,
    solid,
)
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.events import DagsterEventType
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.utils import file_relative_path, safe_tempfile_path


@input_hydration_config(Path)
def df_input_schema(_context, path):
    with open(path, 'r') as fd:
        return [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]


@output_materialization_config(Path)
def df_output_schema(_context, path, value):
    with open(path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return Materialization.file(path)


PoorMansDataFrame = PythonObjectDagsterType(
    python_type=list,
    name='PoorMansDataFrame',
    input_hydration_config=df_input_schema,
    output_materialization_config=df_output_schema,
)


def get_events_of_type(events, event_type):
    return [
        event
        for event in events
        if event.is_dagster_event and event.dagster_event.event_type == event_type
    ]


def test_running():
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'passing_pipeline')
    environment_dict = {
        'solids': {'sum_solid': {'inputs': {'num': file_relative_path(__file__, 'data/num.csv')}}}
    }
    selector = ExecutionSelector('csv_hello_world')

    instance = DagsterInstance.local_temp()
    pipeline_run = instance.create_run_for_pipeline(
        pipeline=passing_pipeline, selector=selector, environment_dict=environment_dict,
    )
    execution_manager = SubprocessExecutionManager(instance)
    execution_manager.execute_pipeline(handle, passing_pipeline, pipeline_run, instance)
    execution_manager.join()
    assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.SUCCESS
    events = instance.all_logs(pipeline_run.run_id)
    assert events

    engine_events = get_events_of_type(events, DagsterEventType.ENGINE_EVENT)
    assert (
        len([ev for ev in engine_events if 'SubprocessExecutionManager' in ev.message]) == 3
    )  # starting, started, exit


def test_failing():
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'failing_pipeline')
    environment_dict = {
        'solids': {'sum_solid': {'inputs': {'num': file_relative_path(__file__, 'data/num.csv')}}}
    }
    selector = ExecutionSelector('csv_hello_world')

    instance = DagsterInstance.local_temp()
    pipeline_run = instance.create_run_for_pipeline(
        pipeline=failing_pipeline, selector=selector, environment_dict=environment_dict,
    )
    execution_manager = SubprocessExecutionManager(instance)
    execution_manager.execute_pipeline(handle, failing_pipeline, pipeline_run, instance)
    execution_manager.join()
    assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.FAILURE
    assert instance.all_logs(pipeline_run.run_id)


def test_execution_crash():
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'crashy_pipeline')
    environment_dict = {
        'solids': {'sum_solid': {'inputs': {'num': file_relative_path(__file__, 'data/num.csv')}}}
    }
    selector = ExecutionSelector('csv_hello_world')

    instance = DagsterInstance.local_temp()
    pipeline_run = instance.create_run_for_pipeline(
        pipeline=crashy_pipeline, selector=selector, environment_dict=environment_dict,
    )
    execution_manager = SubprocessExecutionManager(instance)
    execution_manager.execute_pipeline(handle, crashy_pipeline, pipeline_run, instance)
    execution_manager.join()
    assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.FAILURE
    crash_log = instance.all_logs(pipeline_run.run_id)[
        -2
    ]  # last message is pipeline failure, second to last is...

    assert crash_log.message.startswith(
        '[SubprocessExecutionManager] Pipeline execution process for {run_id} unexpectedly exited'.format(
            run_id=pipeline_run.run_id
        )
    )


@lambda_solid(
    input_defs=[InputDefinition('num', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def sum_solid(num):
    sum_df = deepcopy(num)
    for x in sum_df:
        x['sum'] = x['num1'] + x['num2']
    return sum_df


@lambda_solid(
    input_defs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def error_solid(sum_df):  # pylint: disable=W0613
    raise Exception('foo')


@lambda_solid(
    input_defs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def crashy_solid(sum_df):  # pylint: disable=W0613
    os._exit(1)  # pylint: disable=W0212


@pipeline
def passing_pipeline():
    return sum_solid()


@pipeline
def failing_pipeline():
    return error_solid(sum_solid())


@pipeline
def crashy_pipeline():
    crashy_solid(sum_solid())


@solid(config={'foo': Field(String)})
def node_a(context):
    return context.solid_config['foo']


@solid(config={'bar': Int})
def node_b(context, input_):
    return input_ * context.solid_config['bar']


@composite_solid
def composite_with_nested_config_solid():
    return node_b(node_a())


@pipeline
def composite_pipeline():
    return composite_with_nested_config_solid()


@composite_solid(
    config_fn=lambda cfg: {
        'node_a': {'config': {'foo': cfg['foo']}},
        'node_b': {'config': {'bar': cfg['bar']}},
    },
    config={'foo': Field(String), 'bar': Int},
)
def composite_with_nested_config_solid_and_config_mapping():
    return node_b(node_a())


@pipeline
def composite_pipeline_with_config_mapping():
    return composite_with_nested_config_solid_and_config_mapping()


def test_multiprocessing_execution_for_composite_solid():
    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid': {
                'solids': {'node_a': {'config': {'foo': 'baz'}}, 'node_b': {'config': {'bar': 3}}}
            }
        }
    }

    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'composite_pipeline')

    instance = DagsterInstance.local_temp()
    pipeline_run = instance.create_run_for_pipeline(
        pipeline=composite_pipeline,
        selector=ExecutionSelector('nonce'),
        environment_dict=environment_dict,
    )
    execution_manager = SubprocessExecutionManager(instance)
    execution_manager.execute_pipeline(handle, composite_pipeline, pipeline_run, instance)
    execution_manager.join()
    assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.SUCCESS

    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid': {
                'solids': {'node_a': {'config': {'foo': 'baz'}}, 'node_b': {'config': {'bar': 3}}}
            }
        },
        'execution': {'multiprocess': {}},
        'storage': {'filesystem': {}},
    }

    pipeline_run = instance.create_run_for_pipeline(
        pipeline=composite_pipeline,
        selector=ExecutionSelector('nonce'),
        environment_dict=environment_dict,
    )
    execution_manager = SubprocessExecutionManager(instance)
    execution_manager.execute_pipeline(handle, composite_pipeline, pipeline_run, instance)
    execution_manager.join()


def test_multiprocessing_execution_for_composite_solid_with_config_mapping():
    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid_and_config_mapping': {
                'config': {'foo': 'baz', 'bar': 3}
            }
        }
    }

    handle = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'composite_pipeline_with_config_mapping'
    )

    instance = DagsterInstance.local_temp()
    pipeline_run = instance.create_run_for_pipeline(
        pipeline=composite_pipeline_with_config_mapping, environment_dict=environment_dict,
    )
    execution_manager = SubprocessExecutionManager(instance)
    execution_manager.execute_pipeline(
        handle, composite_pipeline_with_config_mapping, pipeline_run, instance
    )
    execution_manager.join()
    assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.SUCCESS

    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid_and_config_mapping': {
                'config': {'foo': 'baz', 'bar': 3}
            }
        },
        'execution': {'multiprocess': {}},
        'storage': {'filesystem': {}},
    }

    pipeline_run = instance.create_run_for_pipeline(
        pipeline=composite_pipeline_with_config_mapping, environment_dict=environment_dict,
    )
    execution_manager = SubprocessExecutionManager(instance)
    execution_manager.execute_pipeline(
        handle, composite_pipeline_with_config_mapping, pipeline_run, instance
    )

    execution_manager.join()
    assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.SUCCESS


@solid(config={'file': Field(Path)})
def loop(context):
    with open(context.solid_config['file'], 'w') as ff:
        ff.write('yup')

    while True:
        time.sleep(0.1)


@pipeline
def infinite_loop_pipeline():
    loop()


def test_has_run_query_and_terminate():
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'infinite_loop_pipeline')

    instance = DagsterInstance.local_temp()

    with safe_tempfile_path() as path:
        pipeline_run = instance.create_run_for_pipeline(
            pipeline=infinite_loop_pipeline,
            environment_dict={'solids': {'loop': {'config': {'file': path}}}},
        )
        execution_manager = SubprocessExecutionManager(instance)
        execution_manager.execute_pipeline(handle, infinite_loop_pipeline, pipeline_run, instance)

        while not os.path.exists(path):
            time.sleep(0.1)

        assert os.path.exists(path)

        assert execution_manager.is_process_running(pipeline_run.run_id)
        assert execution_manager.terminate(pipeline_run.run_id)
        assert instance.get_run_by_id(pipeline_run.run_id).is_finished
        assert not execution_manager.is_process_running(pipeline_run.run_id)
        assert not execution_manager.terminate(pipeline_run.run_id)

    assert not os.path.exists(path)


def test_two_runs_running():
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'infinite_loop_pipeline')

    with safe_tempfile_path() as file_one, safe_tempfile_path() as file_two:
        instance = DagsterInstance.local_temp()

        execution_manager = SubprocessExecutionManager(instance)

        pipeline_run_one = instance.create_run_for_pipeline(
            pipeline=infinite_loop_pipeline,
            environment_dict={'solids': {'loop': {'config': {'file': file_one}}}},
        )
        execution_manager.execute_pipeline(
            handle, infinite_loop_pipeline, pipeline_run_one, instance
        )

        pipeline_run_two = instance.create_run_for_pipeline(
            pipeline=infinite_loop_pipeline,
            environment_dict={'solids': {'loop': {'config': {'file': file_two}}}},
        )

        execution_manager.execute_pipeline(
            handle, infinite_loop_pipeline, pipeline_run_two, instance
        )

        # ensure both runs have begun execution
        while not os.path.exists(file_one) and not os.path.exists(file_two):
            time.sleep(0.1)

        assert execution_manager.is_process_running(pipeline_run_one.run_id)
        assert execution_manager.is_process_running(pipeline_run_two.run_id)

        assert execution_manager.terminate(pipeline_run_one.run_id)

        assert not execution_manager.is_process_running(pipeline_run_one.run_id)
        assert execution_manager.is_process_running(pipeline_run_two.run_id)

        assert execution_manager.terminate(pipeline_run_two.run_id)

        assert not execution_manager.is_process_running(pipeline_run_one.run_id)
        assert not execution_manager.is_process_running(pipeline_run_two.run_id)


def test_max_concurrency_zero():
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'infinite_loop_pipeline')

    with safe_tempfile_path() as filepath:
        instance = DagsterInstance.local_temp()
        execution_manager = QueueingSubprocessExecutionManager(instance, max_concurrent_runs=0)

        pipeline_run = instance.create_run_for_pipeline(
            pipeline=infinite_loop_pipeline,
            environment_dict={'solids': {'loop': {'config': {'file': filepath}}}},
        )
        execution_manager.execute_pipeline(handle, infinite_loop_pipeline, pipeline_run, instance)
        assert not execution_manager.is_active(pipeline_run.run_id)
        assert not os.path.exists(filepath)


def test_max_concurrency_one():
    handle = ExecutionTargetHandle.for_pipeline_python_file(__file__, 'infinite_loop_pipeline')

    pipeline_def = handle.build_pipeline_definition()

    with safe_tempfile_path() as file_one, safe_tempfile_path() as file_two:
        instance = DagsterInstance.local_temp()
        execution_manager = QueueingSubprocessExecutionManager(instance, max_concurrent_runs=1)

        run_one = instance.create_run_for_pipeline(
            pipeline=pipeline_def,
            environment_dict={'solids': {'loop': {'config': {'file': file_one}}}},
        )
        run_two = instance.create_run_for_pipeline(
            pipeline=pipeline_def,
            environment_dict={'solids': {'loop': {'config': {'file': file_two}}}},
        )

        execution_manager.execute_pipeline(handle, infinite_loop_pipeline, run_one, instance)
        execution_manager.execute_pipeline(handle, infinite_loop_pipeline, run_two, instance)

        while not os.path.exists(file_one):
            execution_manager.check()
            time.sleep(0.1)

        assert execution_manager.is_active(run_one.run_id)
        assert not execution_manager.is_active(run_two.run_id)
        assert not os.path.exists(file_two)

        assert execution_manager.terminate(run_one.run_id)

        while not os.path.exists(file_two):
            execution_manager.check()
            time.sleep(0.1)

        assert not execution_manager.is_active(run_one.run_id)
        assert execution_manager.is_active(run_two.run_id)
        assert execution_manager.terminate(run_two.run_id)
