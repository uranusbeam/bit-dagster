from __future__ import print_function

import os
import random
import string
import sys
import time

import pytest

from dagster import (
    DagsterEventType,
    ExecutionTargetHandle,
    InputDefinition,
    ModeDefinition,
    execute_pipeline,
    pipeline,
    resource,
    solid,
)
from dagster.core.execution.compute_logs import should_disable_io_stream_redirect
from dagster.core.instance import DagsterInstance
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.utils import get_multiprocessing_context

HELLO_SOLID = 'HELLO SOLID'
HELLO_RESOURCE = 'HELLO RESOURCE'
SEPARATOR = os.linesep if (os.name == 'nt' and sys.version_info < (3,)) else '\n'


@resource
def resource_a(_):
    print(HELLO_RESOURCE)
    return 'A'


@solid
def spawn(_):
    return 1


@solid(input_defs=[InputDefinition('num', int)], required_resource_keys={'a'})
def spew(_, num):
    print(HELLO_SOLID)
    return num


def define_pipeline():
    @pipeline(mode_defs=[ModeDefinition(resource_defs={'a': resource_a})])
    def spew_pipeline():
        spew(spew(spawn()))

    return spew_pipeline


def normalize_file_content(s):
    return '\n'.join([line for line in s.replace(os.linesep, '\n').split('\n') if line])


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_compute_log_to_disk():
    spew_pipeline = define_pipeline()
    instance = DagsterInstance.local_temp()
    manager = instance.compute_log_manager
    result = execute_pipeline(spew_pipeline, instance=instance)
    assert result.success

    compute_steps = [
        event.step_key
        for event in result.step_event_list
        if event.event_type == DagsterEventType.STEP_START
    ]
    for step_key in compute_steps:
        if step_key.startswith('spawn'):
            continue
        compute_io_path = manager.get_local_path(result.run_id, step_key, ComputeIOType.STDOUT)
        assert os.path.exists(compute_io_path)
        with open(compute_io_path, 'r') as stdout_file:
            assert normalize_file_content(stdout_file.read()) == HELLO_SOLID


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_compute_log_to_disk_multiprocess():
    spew_pipeline = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'define_pipeline'
    ).build_pipeline_definition()
    instance = DagsterInstance.local_temp()
    manager = instance.compute_log_manager
    result = execute_pipeline(
        spew_pipeline,
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=instance,
    )
    assert result.success

    compute_steps = [
        event.step_key
        for event in result.step_event_list
        if event.event_type == DagsterEventType.STEP_START
    ]
    for step_key in compute_steps:
        if step_key.startswith('spawn'):
            continue
        compute_io_path = manager.get_local_path(result.run_id, step_key, ComputeIOType.STDOUT)
        assert os.path.exists(compute_io_path)
        with open(compute_io_path, 'r') as stdout_file:
            assert normalize_file_content(stdout_file.read()) == HELLO_SOLID


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_compute_log_manager():
    instance = DagsterInstance.local_temp()
    manager = instance.compute_log_manager
    spew_pipeline = define_pipeline()
    result = execute_pipeline(spew_pipeline, instance=instance)
    assert result.success
    compute_steps = [
        event.step_key
        for event in result.step_event_list
        if event.event_type == DagsterEventType.STEP_START
    ]
    assert len(compute_steps) == 3
    step_key = 'spew.compute'
    assert manager.is_watch_completed(result.run_id, step_key)

    stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
    assert normalize_file_content(stdout.data) == HELLO_SOLID

    stderr = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDERR)
    cleaned_logs = stderr.data.replace('\x1b[34m', '').replace('\x1b[0m', '')
    assert 'dagster - DEBUG - spew_pipeline - ' in cleaned_logs

    bad_logs = manager.read_logs_file('not_a_run_id', step_key, ComputeIOType.STDOUT)
    assert bad_logs.data is None
    assert not manager.is_watch_completed('not_a_run_id', step_key)


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_compute_log_manager_subscriptions():
    instance = DagsterInstance.local_temp()
    spew_pipeline = define_pipeline()
    step_key = 'spew.compute'
    result = execute_pipeline(spew_pipeline, instance=instance)
    stdout_observable = instance.compute_log_manager.observable(
        result.run_id, step_key, ComputeIOType.STDOUT
    )
    stderr_observable = instance.compute_log_manager.observable(
        result.run_id, step_key, ComputeIOType.STDERR
    )
    stdout = []
    stdout_observable.subscribe(stdout.append)
    stderr = []
    stderr_observable.subscribe(stderr.append)
    assert len(stdout) == 1
    assert stdout[0].data.startswith(HELLO_SOLID)
    assert stdout[0].cursor in [12, 13]
    assert len(stderr) == 1
    assert stderr[0].cursor == len(stderr[0].data)
    assert stderr[0].cursor > 400


def gen_solid_name(length):
    return ''.join(random.choice(string.ascii_lowercase) for x in range(length))


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_long_solid_names():
    solid_name = gen_solid_name(300)

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'a': resource_a})])
    def long_pipeline():
        spew.alias(name=solid_name)()

    instance = DagsterInstance.local_temp()
    manager = instance.compute_log_manager

    result = execute_pipeline(
        long_pipeline,
        instance=instance,
        environment_dict={'solids': {solid_name: {'inputs': {'num': 1}}}},
    )
    assert result.success

    compute_steps = [
        event.step_key
        for event in result.step_event_list
        if event.event_type == DagsterEventType.STEP_START
    ]

    assert len(compute_steps) == 1
    step_key = compute_steps[0]
    assert manager.is_watch_completed(result.run_id, step_key)

    stdout = manager.read_logs_file(result.run_id, step_key, ComputeIOType.STDOUT)
    assert normalize_file_content(stdout.data) == HELLO_SOLID


def execute_inner(step_key, pipeline_run, instance_ref):
    instance = DagsterInstance.from_ref(instance_ref)
    inner_step(instance, pipeline_run, step_key)


def inner_step(instance, pipeline_run, step_key):
    with instance.compute_log_manager.watch(pipeline_run, step_key=step_key):
        time.sleep(0.1)
        print(step_key, 'inner 1')
        print(step_key, 'inner 2')
        print(step_key, 'inner 3')
        time.sleep(0.1)


def expected_inner_output(step_key):
    return '\n'.join(
        ["{step_key} inner {num}".format(step_key=step_key, num=i + 1) for i in range(3)]
    )


def expected_outer_prefix():
    return '\n'.join(["outer {num}".format(num=i + 1) for i in range(3)])


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_single():
    instance = DagsterInstance.local_temp()
    pipeline_name = 'foo_pipeline'
    pipeline_run = instance.get_or_create_run(pipeline_name=pipeline_name, pipeline_snapshot=None)

    step_keys = ['A', 'B', 'C']

    with instance.compute_log_manager.watch(pipeline_run):
        print('outer 1')
        print('outer 2')
        print('outer 3')

        for step_key in step_keys:
            inner_step(instance, pipeline_run, step_key)

    for step_key in step_keys:
        stdout = instance.compute_log_manager.read_logs_file(
            pipeline_run.run_id, step_key, ComputeIOType.STDOUT
        )
        assert normalize_file_content(stdout.data) == expected_inner_output(step_key)

    full_out = instance.compute_log_manager.read_logs_file(
        pipeline_run.run_id, pipeline_name, ComputeIOType.STDOUT
    )

    assert normalize_file_content(full_out.data).startswith(expected_outer_prefix())


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_multi():
    instance = DagsterInstance.local_temp()
    pipeline_name = 'foo_pipeline'
    pipeline_run = instance.get_or_create_run(pipeline_name=pipeline_name, pipeline_snapshot=None)
    context = get_multiprocessing_context()

    step_keys = ['A', 'B', 'C']

    with instance.compute_log_manager.watch(pipeline_run):
        print('outer 1')
        print('outer 2')
        print('outer 3')

        for step_key in step_keys:
            process = context.Process(
                target=execute_inner, args=(step_key, pipeline_run, instance.get_ref())
            )
            process.start()
            process.join()

    for step_key in step_keys:
        stdout = instance.compute_log_manager.read_logs_file(
            pipeline_run.run_id, step_key, ComputeIOType.STDOUT
        )
        assert normalize_file_content(stdout.data) == expected_inner_output(step_key)

    full_out = instance.compute_log_manager.read_logs_file(
        pipeline_run.run_id, pipeline_name, ComputeIOType.STDOUT
    )

    # The way that the multiprocess compute-logging interacts with pytest (which stubs out the
    # sys.stdout fileno) makes this difficult to test.  The pytest-captured stdout only captures
    # the stdout from the outer process, not also the inner process
    assert normalize_file_content(full_out.data).startswith(expected_outer_prefix())
