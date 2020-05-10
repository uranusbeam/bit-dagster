import os

import yaml

from dagster import __version__ as dagster_version
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils import load_yaml_from_path

from .conftest import docker_image  # pylint: disable=unused-import
from .utils import environments_path, remove_none_recursively, wait_for_job_and_get_logs

EXPECTED_JOB_SPEC = '''
api_version: batch/v1
kind: Job
metadata:
  labels:
    app.kubernetes.io/instance: dagster
    app.kubernetes.io/name: dagster
    app.kubernetes.io/version: {dagster_version}
  name: dagster-job-{run_id}
spec:
  backoff_limit: 4
  template:
    metadata:
      labels:
        app.kubernetes.io/instance: dagster
        app.kubernetes.io/name: dagster
        app.kubernetes.io/version: {dagster_version}
      name: dagster-job-pod-{run_id}
    spec:
      containers:
      - args:
        - -p
        - startPipelineExecutionForCreatedRun
        - -v
        - '{{"runId": "{run_id}"}}'
        command:
        - dagster-graphql
        env:
        - name: DAGSTER_PG_PASSWORD
          value_from:
            secret_key_ref:
              key: postgresql-password
              name: dagster-postgresql-secret
        env_from:
        - config_map_ref:
            name: dagster-job-runner-env
        - config_map_ref:
            name: test-env-configmap
        - secret_ref:
            name: test-env-secret
        image: {job_image}
        image_pull_policy: {image_pull_policy}
        name: dagster-job-{run_id}
        volume_mounts:
        - mount_path: /opt/dagster/dagster_home/dagster.yaml
          name: dagster-instance
          sub_path: dagster.yaml
      image_pull_secrets:
      - name: element-dev-key
      restart_policy: Never
      service_account_name: dagit-admin
      volumes:
      - config_map:
          name: dagster-instance
        name: dagster-instance
  ttl_seconds_after_finished: 100
'''


def test_valid_job_format(
    docker_image, image_pull_policy, run_launcher
):  # pylint: disable=redefined-outer-name
    environment_dict = load_yaml_from_path(os.path.join(environments_path(), 'env.yaml'))
    pipeline_name = 'demo_pipeline'
    run = PipelineRun(pipeline_name=pipeline_name, environment_dict=environment_dict)

    job = run_launcher.construct_job(run)

    assert (
        yaml.dump(remove_none_recursively(job.to_dict()), default_flow_style=False).strip()
        == EXPECTED_JOB_SPEC.format(
            run_id=run.run_id,
            job_image=docker_image,
            image_pull_policy=image_pull_policy,
            dagster_version=dagster_version,
        ).strip()
    )


def test_k8s_run_launcher(dagster_instance, helm_namespace):  # pylint: disable=redefined-outer-name
    environment_dict = load_yaml_from_path(os.path.join(environments_path(), 'env.yaml'))
    pipeline_name = 'demo_pipeline'
    run = dagster_instance.get_or_create_run(
        pipeline_name=pipeline_name, environment_dict=environment_dict, mode='default'
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
