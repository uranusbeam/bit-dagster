import pytest

from dagster import (
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    String,
    execute_pipeline,
    input_hydration_config,
    output_materialization_config,
    pipeline,
    resource,
    solid,
    usable_as_dagster_type,
)
from dagster.core.storage.type_storage import TypeStoragePlugin
from dagster.core.types.dagster_type import create_any_type


class UserError(Exception):
    def __init__(self):
        super(UserError, self).__init__('The user has errored')


def test_user_error_boundary_solid_compute():
    @solid
    def throws_user_error(_):
        raise UserError()

    @pipeline
    def pipeline_def():
        throws_user_error()

    pipeline_result = execute_pipeline(pipeline_def, raise_on_error=False)
    assert not pipeline_result.success


def test_user_error_boundary_input_hydration():
    @input_hydration_config(String)
    def InputHydration(context, hello):
        raise UserError()

    @usable_as_dagster_type(input_hydration_config=InputHydration)
    class CustomType(str):
        pass

    @solid(input_defs=[InputDefinition('custom_type', CustomType)])
    def input_hydration_solid(context, custom_type):
        context.log.info(custom_type)

    @pipeline
    def input_hydration_pipeline():
        input_hydration_solid()

    pipeline_result = execute_pipeline(
        input_hydration_pipeline,
        {'solids': {'input_hydration_solid': {'inputs': {'custom_type': 'hello'}}}},
        raise_on_error=False,
    )
    assert not pipeline_result.success


def test_user_error_boundary_output_materialization():
    @output_materialization_config(String)
    def materialize(context, *_args, **_kwargs):
        raise UserError()

    CustomDagsterType = create_any_type(
        name='CustomType', output_materialization_config=materialize
    )

    @solid(output_defs=[OutputDefinition(CustomDagsterType)])
    def output_solid(_context):
        return 'hello'

    @pipeline
    def output_materialization_pipeline():
        output_solid()

    pipeline_result = execute_pipeline(
        output_materialization_pipeline,
        {'solids': {'output_solid': {'outputs': [{'result': 'hello'}]}}},
        raise_on_error=False,
    )
    assert not pipeline_result.success


def test_user_error_boundary_resource_init():
    @resource
    def resource_a(_):
        raise UserError()

    @solid(required_resource_keys={'a'})
    def resource_solid(_context):
        return 'hello'

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'a': resource_a})])
    def resource_pipeline():
        resource_solid()

    pipeline_result = execute_pipeline(resource_pipeline, raise_on_error=False)
    assert not pipeline_result.success


@pytest.mark.skip('not implemented')
def test_user_error_boundary_storage_plugin():
    class CustomStoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
        @classmethod
        def compatible_with_storage_def(cls, system_storage_def):
            return True

        @classmethod
        def set_object(cls, intermediate_store, obj, context, dagster_type, paths):
            raise UserError()

        @classmethod
        def get_object(cls, intermediate_store, context, dagster_type, paths):
            raise UserError()

    CustomDagsterType = create_any_type(name='CustomType', auto_plugins=[CustomStoragePlugin])

    @solid(output_defs=[OutputDefinition(CustomDagsterType)])
    def output_solid(_context):
        return 'hello'

    @pipeline
    def plugin_pipeline():
        output_solid()

    pipeline_result = execute_pipeline(
        plugin_pipeline, {'storage': {'filesystem': {}}}, raise_on_error=False
    )
    assert not pipeline_result.success
