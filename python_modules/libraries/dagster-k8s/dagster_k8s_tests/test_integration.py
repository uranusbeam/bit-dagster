import os

import pytest
from dagster_k8s import get_celery_engine_config

from dagster.utils import load_yaml_from_path, merge_dicts
from dagster.utils.yaml_utils import merge_yamls

from .utils import environments_path, wait_for_job_and_get_logs


@pytest.mark.integration
def test_k8s_run_launcher_default(
    dagster_instance, helm_namespace
):  # pylint: disable=redefined-outer-name
    environment_dict = load_yaml_from_path(os.path.join(environments_path(), 'env.yaml'))
    pipeline_name = 'demo_pipeline'
    tags = {'key': 'value'}
    run = dagster_instance.get_or_create_run(
        pipeline_name=pipeline_name, environment_dict=environment_dict, tags=tags, mode='default'
    )

    dagster_instance.launch_run(run)

    result = wait_for_job_and_get_logs(
        job_name='dagster-job-%s' % run.run_id, namespace=helm_namespace
    )

    assert not result.get('errors')
    assert result['data']
    assert (
        result['data']['startPipelineExecutionForCreatedRun']['__typename']
        == 'StartPipelineRunSuccess'
    )
    assert 'PipelineSuccessEvent' in {
        log['__typename']: log
        for log in result['data']['startPipelineExecutionForCreatedRun']['run']['logs']['nodes']
    }


@pytest.mark.integration
def test_k8s_run_launcher_celery(
    dagster_instance, helm_namespace
):  # pylint: disable=redefined-outer-name
    environment_dict = merge_dicts(
        merge_yamls(
            [
                os.path.join(environments_path(), 'env.yaml'),
                os.path.join(environments_path(), 'env_filesystem.yaml'),
            ]
        ),
        get_celery_engine_config(),
    )

    assert 'celery' in environment_dict['execution']

    pipeline_name = 'demo_pipeline_celery'
    tags = {'key': 'value'}
    run = dagster_instance.get_or_create_run(
        pipeline_name=pipeline_name, environment_dict=environment_dict, tags=tags, mode='default'
    )

    dagster_instance.launch_run(run)
    result = wait_for_job_and_get_logs(
        job_name='dagster-job-%s' % run.run_id, namespace=helm_namespace
    )

    assert not result.get('errors')
    assert result['data']
    # this is bad test but proves that we got celery configured properly
    # to get it working would involve relying on s3 / gcs for storage
    assert result['data']['startPipelineExecutionForCreatedRun']['__typename'] == 'PythonError'
    assert (
        'Must use S3 or GCS storage with non-local Celery broker: pyamqp://test:test@dagster-rabbitmq:5672// and backend: amqp'
        in result['data']['startPipelineExecutionForCreatedRun']['message']
    )


@pytest.mark.integration
def test_failing_k8s_run_launcher(dagster_instance, helm_namespace):
    environment_dict = {'blah blah this is wrong': {}}
    pipeline_name = 'demo_pipeline'
    run = dagster_instance.get_or_create_run(
        pipeline_name=pipeline_name, environment_dict=environment_dict
    )

    dagster_instance.launch_run(run)
    result = wait_for_job_and_get_logs(
        job_name='dagster-job-%s' % run.run_id, namespace=helm_namespace
    )

    assert not result.get('errors')
    assert result['data']
    assert (
        result['data']['startPipelineExecutionForCreatedRun']['__typename']
        == 'PipelineConfigValidationInvalid'
    )
    assert len(result['data']['startPipelineExecutionForCreatedRun']['errors']) == 2

    assert set(
        error['reason'] for error in result['data']['startPipelineExecutionForCreatedRun']['errors']
    ) == {'FIELD_NOT_DEFINED', 'MISSING_REQUIRED_FIELD',}
