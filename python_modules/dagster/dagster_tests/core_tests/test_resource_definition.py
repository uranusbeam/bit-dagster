import pytest

from dagster import (
    DagsterEventType,
    DagsterResourceFunctionError,
    ExecutionTargetHandle,
    Field,
    Int,
    ModeDefinition,
    PipelineDefinition,
    ResourceDefinition,
    String,
    execute_pipeline,
    execute_pipeline_iterator,
    resource,
    solid,
)
from dagster.core.events.log import EventRecord, LogMessageRecord, construct_event_logger
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.config import RunConfig
from dagster.core.instance import DagsterInstance


def define_string_resource():
    return ResourceDefinition(
        config=String, resource_fn=lambda init_context: init_context.resource_config
    )


def test_basic_resource():
    called = {}

    @solid(required_resource_keys={'a_string'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.a_string == 'foo'

    pipeline_def = PipelineDefinition(
        name='with_a_resource',
        solid_defs=[a_solid],
        mode_defs=[ModeDefinition(resource_defs={'a_string': define_string_resource()})],
    )

    result = execute_pipeline(pipeline_def, {'resources': {'a_string': {'config': 'foo'}}})

    assert result.success
    assert called['yup']


def test_yield_resource():
    called = {}

    @solid(required_resource_keys={'a_string'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.a_string == 'foo'

    def _do_resource(init_context):
        yield init_context.resource_config

    yield_string_resource = ResourceDefinition(config=String, resource_fn=_do_resource)

    pipeline_def = PipelineDefinition(
        name='with_a_yield_resource',
        solid_defs=[a_solid],
        mode_defs=[ModeDefinition(resource_defs={'a_string': yield_string_resource})],
    )

    result = execute_pipeline(pipeline_def, {'resources': {'a_string': {'config': 'foo'}}})

    assert result.success
    assert called['yup']


def test_yield_multiple_resources():
    called = {}

    saw = []

    @solid(required_resource_keys={'string_one', 'string_two'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.string_one == 'foo'
        assert context.resources.string_two == 'bar'

    def _do_resource(init_context):
        saw.append('before yield ' + init_context.resource_config)
        yield init_context.resource_config
        saw.append('after yield ' + init_context.resource_config)

    yield_string_resource = ResourceDefinition(config=String, resource_fn=_do_resource)

    pipeline_def = PipelineDefinition(
        name='with_yield_resources',
        solid_defs=[a_solid],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'string_one': yield_string_resource,
                    'string_two': yield_string_resource,
                }
            )
        ],
    )

    result = execute_pipeline(
        pipeline_def,
        {'resources': {'string_one': {'config': 'foo'}, 'string_two': {'config': 'bar'}}},
    )

    assert result.success
    assert called['yup']
    assert len(saw) == 4

    assert 'before yield' in saw[0]
    assert 'before yield' in saw[1]
    assert 'after yield' in saw[2]
    assert 'after yield' in saw[3]


def test_resource_decorator():
    called = {}

    saw = []

    @solid(required_resource_keys={'string_one', 'string_two'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.string_one == 'foo'
        assert context.resources.string_two == 'bar'

    # API red alert. One has to wrap a type in Field because it is callable
    @resource(config=Field(String))
    def yielding_string_resource(init_context):
        saw.append('before yield ' + init_context.resource_config)
        yield init_context.resource_config
        saw.append('after yield ' + init_context.resource_config)

    pipeline_def = PipelineDefinition(
        name='with_yield_resources',
        solid_defs=[a_solid],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'string_one': yielding_string_resource,
                    'string_two': yielding_string_resource,
                }
            )
        ],
    )

    result = execute_pipeline(
        pipeline_def,
        {'resources': {'string_one': {'config': 'foo'}, 'string_two': {'config': 'bar'}}},
    )

    assert result.success
    assert called['yup']
    assert len(saw) == 4

    assert 'before yield' in saw[0]
    assert 'before yield' in saw[1]
    assert 'after yield' in saw[2]
    assert 'after yield' in saw[3]


def test_mixed_multiple_resources():
    called = {}

    saw = []

    @solid(required_resource_keys={'returned_string', 'yielded_string'})
    def a_solid(context):
        called['yup'] = True
        assert context.resources.returned_string == 'foo'
        assert context.resources.yielded_string == 'bar'

    def _do_yield_resource(init_context):
        saw.append('before yield ' + init_context.resource_config)
        yield init_context.resource_config
        saw.append('after yield ' + init_context.resource_config)

    yield_string_resource = ResourceDefinition(config=String, resource_fn=_do_yield_resource)

    def _do_return_resource(init_context):
        saw.append('before return ' + init_context.resource_config)
        return init_context.resource_config

    return_string_resource = ResourceDefinition(config=String, resource_fn=_do_return_resource)

    pipeline_def = PipelineDefinition(
        name='with_a_yield_resource',
        solid_defs=[a_solid],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'yielded_string': yield_string_resource,
                    'returned_string': return_string_resource,
                }
            )
        ],
    )

    result = execute_pipeline(
        pipeline_def,
        {'resources': {'returned_string': {'config': 'foo'}, 'yielded_string': {'config': 'bar'}}},
    )

    assert result.success
    assert called['yup']
    # could be processed in any order in python 2
    assert 'before yield bar' in saw[0] or 'before return foo' in saw[0]
    assert 'before yield bar' in saw[1] or 'before return foo' in saw[1]
    assert 'after yield bar' in saw[2]


def test_none_resource():
    called = {}

    @solid(required_resource_keys={'test_null'})
    def solid_test_null(context):
        assert context.resources.test_null is None
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='test_none_resource',
        solid_defs=[solid_test_null],
        mode_defs=[ModeDefinition(resource_defs={'test_null': ResourceDefinition.none_resource()})],
    )

    result = execute_pipeline(pipeline)

    assert result.success
    assert called['yup']


def test_string_resource():
    called = {}

    @solid(required_resource_keys={'test_string'})
    def solid_test_string(context):
        assert context.resources.test_string == 'foo'
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='test_string_resource',
        solid_defs=[solid_test_string],
        mode_defs=[
            ModeDefinition(resource_defs={'test_string': ResourceDefinition.string_resource()})
        ],
    )

    result = execute_pipeline(pipeline, {'resources': {'test_string': {'config': 'foo'}}})

    assert result.success
    assert called['yup']


def test_no_config_resource_pass_none():
    called = {}

    @resource(None)
    def return_thing(_init_context):
        called['resource'] = True
        return 'thing'

    @solid(required_resource_keys={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solid_defs=[check_thing],
        mode_defs=[ModeDefinition(resource_defs={'return_thing': return_thing})],
    )

    execute_pipeline(pipeline)

    assert called['resource']
    assert called['solid']


def test_no_config_resource_no_arg():
    called = {}

    @resource()
    def return_thing(_init_context):
        called['resource'] = True
        return 'thing'

    @solid(required_resource_keys={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solid_defs=[check_thing],
        mode_defs=[ModeDefinition(resource_defs={'return_thing': return_thing})],
    )

    execute_pipeline(pipeline)

    assert called['resource']
    assert called['solid']


def test_no_config_resource_bare_no_arg():
    called = {}

    @resource
    def return_thing(_init_context):
        called['resource'] = True
        return 'thing'

    @solid(required_resource_keys={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solid_defs=[check_thing],
        mode_defs=[ModeDefinition(resource_defs={'return_thing': return_thing})],
    )

    execute_pipeline(pipeline)

    assert called['resource']
    assert called['solid']


def test_no_config_resource_definition():
    called = {}

    def _return_thing_resource_fn(_init_context):
        called['resource'] = True
        return 'thing'

    @solid(required_resource_keys={'return_thing'})
    def check_thing(context):
        called['solid'] = True
        assert context.resources.return_thing == 'thing'

    pipeline = PipelineDefinition(
        name='test_no_config_resource',
        solid_defs=[check_thing],
        mode_defs=[
            ModeDefinition(
                resource_defs={'return_thing': ResourceDefinition(_return_thing_resource_fn)}
            )
        ],
    )

    execute_pipeline(pipeline)

    assert called['resource']
    assert called['solid']


def test_resource_cleanup():
    called = {}

    def _cleanup_resource_fn(_init_context):
        called['creation'] = True
        yield True
        called['cleanup'] = True

    @solid(required_resource_keys={'resource_with_cleanup'})
    def check_resource_created(context):
        called['solid'] = True
        assert context.resources.resource_with_cleanup is True

    pipeline = PipelineDefinition(
        name='test_resource_cleanup',
        solid_defs=[check_resource_created],
        mode_defs=[
            ModeDefinition(
                resource_defs={'resource_with_cleanup': ResourceDefinition(_cleanup_resource_fn)}
            )
        ],
    )

    execute_pipeline(pipeline)

    assert called['creation'] is True
    assert called['solid'] is True
    assert called['cleanup'] is True


def test_stacked_resource_cleanup():
    called = []

    def _cleanup_resource_fn_1(_init_context):
        called.append('creation_1')
        yield True
        called.append('cleanup_1')

    def _cleanup_resource_fn_2(_init_context):
        called.append('creation_2')
        yield True
        called.append('cleanup_2')

    @solid(required_resource_keys={'resource_with_cleanup_1', 'resource_with_cleanup_2'})
    def check_resource_created(context):
        called.append('solid')
        assert context.resources.resource_with_cleanup_1 is True
        assert context.resources.resource_with_cleanup_2 is True

    pipeline = PipelineDefinition(
        name='test_resource_cleanup',
        solid_defs=[check_resource_created],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'resource_with_cleanup_1': ResourceDefinition(_cleanup_resource_fn_1),
                    'resource_with_cleanup_2': ResourceDefinition(_cleanup_resource_fn_2),
                }
            )
        ],
    )

    execute_pipeline(pipeline)

    assert called == ['creation_1', 'creation_2', 'solid', 'cleanup_2', 'cleanup_1']


def test_resource_init_failure():
    @resource
    def failing_resource(_init_context):
        raise Exception('Uh oh')

    @solid(required_resource_keys={'failing_resource'})
    def failing_resource_solid(_context):
        pass

    pipeline = PipelineDefinition(
        name='test_resource_init_failure',
        solid_defs=[failing_resource_solid],
        mode_defs=[ModeDefinition(resource_defs={'failing_resource': failing_resource})],
    )

    res = execute_pipeline(pipeline, raise_on_error=False)

    event_types = [event.event_type_value for event in res.event_list]
    assert DagsterEventType.PIPELINE_INIT_FAILURE.value in event_types

    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline)
    pipeline_run = instance.create_run_for_pipeline(pipeline, execution_plan=execution_plan)

    step_events = execute_plan(execution_plan, pipeline_run=pipeline_run, instance=instance)

    event_types = [event.event_type_value for event in step_events]
    assert DagsterEventType.PIPELINE_INIT_FAILURE.value in event_types

    # Test the pipeline init failure event fires even if we are raising errors
    events = []
    try:
        for event in execute_pipeline_iterator(pipeline):
            events.append(event)
    except DagsterResourceFunctionError:
        pass

    event_types = [event.event_type_value for event in events]
    assert DagsterEventType.PIPELINE_INIT_FAILURE.value in event_types


def test_dagster_type_resource_decorator_config():
    @resource(Int)
    def dagster_type_resource_config(_):
        raise Exception('not called')

    assert dagster_type_resource_config.config_field.config_type.given_name == 'Int'

    @resource(int)
    def python_type_resource_config(_):
        raise Exception('not called')

    assert python_type_resource_config.config_field.config_type.given_name == 'Int'


def test_resource_init_failure_with_teardown():
    called = []
    cleaned = []

    @resource
    def resource_a(_):
        try:
            called.append('A')
            yield 'A'
        finally:
            cleaned.append('A')

    @resource
    def resource_b(_):
        try:
            called.append('B')
            raise Exception('uh oh')
            yield 'B'  # pylint: disable=unreachable
        finally:
            cleaned.append('B')

    @solid(required_resource_keys={'a', 'b'})
    def resource_solid(_):
        pass

    pipeline = PipelineDefinition(
        name='test_resource_init_failure_with_cleanup',
        solid_defs=[resource_solid],
        mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b})],
    )

    res = execute_pipeline(pipeline, raise_on_error=False)
    event_types = [event.event_type_value for event in res.event_list]
    assert DagsterEventType.PIPELINE_INIT_FAILURE.value in event_types

    assert called == ['A', 'B']
    assert cleaned == ['B', 'A']

    called = []
    cleaned = []

    events = []
    try:
        for event in execute_pipeline_iterator(pipeline):
            events.append(event)
    except DagsterResourceFunctionError:
        pass

    event_types = [event.event_type_value for event in events]
    assert DagsterEventType.PIPELINE_INIT_FAILURE.value in event_types
    assert called == ['A', 'B']
    assert cleaned == ['B', 'A']


def test_solid_failure_resource_teardown():
    called = []
    cleaned = []

    @resource
    def resource_a(_):
        try:
            called.append('A')
            yield 'A'
        finally:
            cleaned.append('A')

    @resource
    def resource_b(_):
        try:
            called.append('B')
            yield 'B'
        finally:
            cleaned.append('B')

    @solid(required_resource_keys={'a', 'b'})
    def resource_solid(_):
        raise Exception('uh oh')

    pipeline = PipelineDefinition(
        name='test_solid_failure_resource_teardown',
        solid_defs=[resource_solid],
        mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b})],
    )

    res = execute_pipeline(pipeline, raise_on_error=False)
    assert res.event_list[-1].event_type_value == 'PIPELINE_FAILURE'
    assert called == ['A', 'B']
    assert cleaned == ['B', 'A']

    called = []
    cleaned = []

    events = []
    try:
        for event in execute_pipeline_iterator(pipeline):
            events.append(event)
    except DagsterResourceFunctionError:
        pass

    assert len(events) > 1
    assert events[-1].event_type_value == 'PIPELINE_FAILURE'
    assert called == ['A', 'B']
    assert cleaned == ['B', 'A']


def test_solid_failure_resource_teardown_raise():
    ''' test that teardown is invoked in resources for tests that raise_on_error '''
    called = []
    cleaned = []

    @resource
    def resource_a(_):
        try:
            called.append('A')
            yield 'A'
        finally:
            cleaned.append('A')

    @resource
    def resource_b(_):
        try:
            called.append('B')
            yield 'B'
        finally:
            cleaned.append('B')

    @solid(required_resource_keys={'a', 'b'})
    def resource_solid(_):
        raise Exception('uh oh')

    pipeline = PipelineDefinition(
        name='test_solid_failure_resource_teardown',
        solid_defs=[resource_solid],
        mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b})],
    )

    with pytest.raises(Exception) as exc_info:
        execute_pipeline(pipeline)

    assert called == ['A', 'B']
    assert cleaned == ['B', 'A']

    called = []
    cleaned = []


def test_resource_teardown_failure():
    called = []
    cleaned = []

    @resource
    def resource_a(_):
        try:
            called.append('A')
            yield 'A'
        finally:
            cleaned.append('A')

    @resource
    def resource_b(_):
        try:
            called.append('B')
            yield 'B'
        finally:
            raise Exception('uh oh')
            cleaned.append('B')  # pylint: disable=unreachable

    @solid(required_resource_keys={'a', 'b'})
    def resource_solid(_):
        pass

    pipeline = PipelineDefinition(
        name='test_resource_teardown_failure',
        solid_defs=[resource_solid],
        mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b})],
    )

    result = execute_pipeline(pipeline, raise_on_error=False)
    assert result.success
    error_events = [
        event
        for event in result.event_list
        if event.is_engine_event and event.event_specific_data.error
    ]
    assert len(error_events) == 1
    assert called == ['A', 'B']
    assert cleaned == ['A']

    called = []
    cleaned = []
    events = []
    try:
        for event in execute_pipeline_iterator(pipeline):
            events.append(event)
    except DagsterResourceFunctionError:
        pass

    assert called == ['A', 'B']
    assert cleaned == ['A']


def define_resource_teardown_failure_pipeline():
    @resource
    def resource_a(_):
        try:
            yield 'A'
        finally:
            pass

    @resource
    def resource_b(_):
        try:
            yield 'B'
        finally:
            raise Exception('uh oh')

    @solid(required_resource_keys={'a', 'b'})
    def resource_solid(_):
        pass

    return PipelineDefinition(
        name='resource_teardown_failure',
        solid_defs=[resource_solid],
        mode_defs=[ModeDefinition(resource_defs={'a': resource_a, 'b': resource_b})],
    )


def test_multiprocessing_resource_teardown_failure():
    pipeline = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'define_resource_teardown_failure_pipeline'
    ).build_pipeline_definition()
    result = execute_pipeline(
        pipeline,
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=DagsterInstance.local_temp(),
        raise_on_error=False,
    )
    assert result.success
    error_events = [
        event
        for event in result.event_list
        if event.is_engine_event and event.event_specific_data.error
    ]
    assert len(error_events) > 1


def test_single_step_resource_event_logs():
    # Test to attribute logs for single-step plans which are often the representation of
    # sub-plans in a multiprocessing execution environment. Most likely will need to be rewritten
    # with the refactor detailed in https://github.com/dagster-io/dagster/issues/2239
    USER_SOLID_MESSAGE = 'I AM A SOLID'
    USER_RESOURCE_MESSAGE = 'I AM A RESOURCE'
    events = []

    def event_callback(record):
        assert isinstance(record, EventRecord)
        events.append(record)

    @solid(required_resource_keys={'a'})
    def resource_solid(context):
        context.log.info(USER_SOLID_MESSAGE)

    @resource
    def resource_a(context):
        context.log.info(USER_RESOURCE_MESSAGE)
        return 'A'

    pipeline = PipelineDefinition(
        name='resource_logging_pipeline',
        solid_defs=[resource_solid],
        mode_defs=[
            ModeDefinition(
                resource_defs={'a': resource_a},
                logger_defs={'callback': construct_event_logger(event_callback)},
            )
        ],
    )

    result = execute_pipeline(
        pipeline,
        environment_dict={'loggers': {'callback': {}},},
        instance=DagsterInstance.local_temp(),
        run_config=RunConfig(step_keys_to_execute=['resource_solid.compute']),
    )
    assert result.success
    log_messages = [event for event in events if isinstance(event, LogMessageRecord)]
    assert len(log_messages) == 2

    resource_log_message = next(
        iter([message for message in log_messages if message.user_message == USER_RESOURCE_MESSAGE])
    )
    assert resource_log_message.step_key == 'resource_solid.compute'
