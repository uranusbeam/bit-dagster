from dagster import execute_pipeline


def test_example_bash_command_solid():
    from .example_bash_command_solid import pipe

    res = execute_pipeline(pipe)
    assert res.success
    assert res.result_for_solid('a').output_value() == 'hello, world!\n'


def test_example_bash_script_solid():
    from .example_bash_script_solid import pipe

    res = execute_pipeline(pipe)
    assert res.success
    assert res.result_for_solid('a').output_value() == 'hello, world!\n'
