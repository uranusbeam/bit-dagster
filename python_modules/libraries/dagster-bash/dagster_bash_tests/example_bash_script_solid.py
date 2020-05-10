from dagster_bash import bash_script_solid

from dagster import file_relative_path, pipeline


@pipeline
def pipe():
    a = bash_script_solid(file_relative_path(__file__, 'hello_world.sh'), name='a')
    a()
