from dagster_pyspark import pyspark_resource, pyspark_solid

from dagster import Field, InputDefinition, ModeDefinition, execute_pipeline, pipeline, solid


def test_simple_pyspark_decorator():
    @pyspark_solid
    def pyspark_job(context):
        rdd = context.resources.pyspark.spark_context.parallelize(range(10))
        for item in rdd.collect():
            print(item)

    @pipeline(mode_defs=[ModeDefinition('default', resource_defs={'pyspark': pyspark_resource})])
    def pipe():
        pyspark_job()

    assert execute_pipeline(pipeline=pipe, mode='default').success


def test_pyspark_decorator_with_arguments():
    @solid
    def produce_number(_):
        return 10

    @pyspark_solid(input_defs=[InputDefinition('count', int)])
    def pyspark_job(context, count):
        rdd = context.resources.pyspark.spark_context.parallelize(range(count))
        for item in rdd.collect():
            print(item)

    @pipeline(mode_defs=[ModeDefinition('default', resource_defs={'pyspark': pyspark_resource})])
    def pipe():
        pyspark_job(produce_number())

    assert execute_pipeline(pipeline=pipe, mode='default').success


def test_named_pyspark_decorator():
    @pyspark_solid(name='blah', description='foo bar', config={'foo': Field(str)})
    def pyspark_job(context):
        rdd = context.resources.pyspark.spark_context.parallelize(range(10))
        for item in rdd.collect():
            print(item)

    @pipeline(mode_defs=[ModeDefinition('default', resource_defs={'pyspark': pyspark_resource})])
    def pipe():
        pyspark_job()

    assert execute_pipeline(
        pipeline=pipe,
        mode='default',
        environment_dict={'solids': {'blah': {'config': {'foo': 'baz'}}}},
    ).success


def test_default_pyspark_decorator():
    @pyspark_solid(pyspark_resource_key='first_pyspark')
    def first_pyspark_job(context):
        list_p = [('Michelle', 19), ('Austin', 29), ('Lydia', 35)]
        rdd = context.resources.first_pyspark.spark_context.parallelize(list_p)
        res = rdd.take(2)
        for name, age in res:
            print('%s: %d' % (name, age))

    @pyspark_solid(pyspark_resource_key='last_pyspark')
    def last_pyspark_job(context):
        list_p = [('John', 19), ('Jennifer', 29), ('Adam', 35), ('Henry', 50)]
        rdd = context.resources.last_pyspark.spark_context.parallelize(list_p)
        res = rdd.take(2)
        for name, age in res:
            print('%s: %d' % (name, age))

    @pipeline(
        mode_defs=[
            ModeDefinition(
                'default',
                resource_defs={'first_pyspark': pyspark_resource, 'last_pyspark': pyspark_resource},
            )
        ]
    )
    def pipe():
        first_pyspark_job()
        last_pyspark_job()

    assert execute_pipeline(pipeline=pipe, mode='default').success


def test_aliased_pyspark_solid():
    @pyspark_solid
    def pyspark_job(context):
        list_p = [('Michelle', 19), ('Austin', 29), ('Lydia', 35)]
        rdd = context.resources.pyspark.spark_context.parallelize(list_p)
        res = rdd.take(2)
        for name, age in res:
            print('%s: %d' % (name, age))
        return context.solid.name

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'pyspark': pyspark_resource})])
    def pipe():
        pyspark_job.alias('new_pyspark_solid')()

    res = execute_pipeline(pipe)
    assert res.success

    assert res.result_for_solid('new_pyspark_solid').output_value() == 'new_pyspark_solid'
