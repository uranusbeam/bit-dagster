from dagster import check
from dagster.core.definitions import ExpectationResult, Materialization, Output, Solid, SolidHandle
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.context.compute import SolidExecutionContext
from dagster.core.execution.context.system import SystemComputeExecutionContext

from .objects import ExecutionStep, StepInput, StepKind, StepOutput


def create_compute_step(pipeline_name, environment_config, solid, step_inputs, handle):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(solid, 'solid', Solid)
    check.list_param(step_inputs, 'step_inputs', of_type=StepInput)
    check.opt_inst_param(handle, 'handle', SolidHandle)

    # the environment config has the solid output name configured
    config_output_names = set()
    current_handle = handle
    while current_handle:
        solid_config = environment_config.solids.get(current_handle.to_string())
        current_handle = current_handle.parent
        for output_spec in solid_config.outputs:
            config_output_names = config_output_names.union(output_spec.keys())

    return ExecutionStep(
        pipeline_name=pipeline_name,
        key_suffix='compute',
        step_inputs=step_inputs,
        step_outputs=[
            StepOutput(
                name=name,
                dagster_type=output_def.dagster_type,
                optional=output_def.optional,
                should_materialize=name in config_output_names,
            )
            for name, output_def in solid.definition.output_dict.items()
        ],
        compute_fn=lambda step_context, inputs: _execute_core_compute(
            step_context.for_compute(), inputs, solid.definition.compute_fn
        ),
        kind=StepKind.COMPUTE,
        solid_handle=handle,
        tags=solid.tags,
    )


def _yield_compute_results(compute_context, inputs, compute_fn):
    check.inst_param(compute_context, 'compute_context', SystemComputeExecutionContext)
    step = compute_context.step
    user_event_sequence = compute_fn(SolidExecutionContext(compute_context), inputs)

    if isinstance(user_event_sequence, Output):
        raise DagsterInvariantViolationError(
            (
                'Compute function for solid {solid_name} returned a Output rather than '
                'yielding it. The compute_fn of the core SolidDefinition must yield '
                'its results'
            ).format(solid_name=str(step.solid_handle))
        )

    if user_event_sequence is None:
        return

    for event in user_event_sequence:
        if isinstance(event, (Output, Materialization, ExpectationResult)):
            yield event
        else:
            raise DagsterInvariantViolationError(
                (
                    'Compute function for solid {solid_name} yielded a value of type {type_} '
                    'rather than an instance of Output, Materialization, or ExpectationResult. '
                    'Values yielded by solids must be wrapped in one of these types. If your '
                    'solid has a single output and yields no other events, you may want to use '
                    '`return` instead of `yield` in the body of your solid compute function. If '
                    'you are already using `return`, and you expected to return a value of type '
                    '{type_}, you may be inadvertently returning a generator rather than the value '
                    'you expected.'
                ).format(solid_name=str(step.solid_handle), type_=type(event))
            )


def _execute_core_compute(compute_context, inputs, compute_fn):
    '''
    Execute the user-specified compute for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(compute_context, 'compute_context', SystemComputeExecutionContext)
    check.dict_param(inputs, 'inputs', key_type=str)

    step = compute_context.step

    all_results = []
    for step_output in _yield_compute_results(compute_context, inputs, compute_fn):
        yield step_output
        if isinstance(step_output, Output):
            all_results.append(step_output)

    if len(all_results) != len(step.step_outputs):
        emitted_result_names = {r.output_name for r in all_results}
        solid_output_names = {output.name for output in step.step_outputs}
        omitted_outputs = solid_output_names.difference(emitted_result_names)
        compute_context.log.info(
            'Solid {solid} did not fire outputs {outputs}'.format(
                solid=str(step.solid_handle), outputs=repr(omitted_outputs)
            )
        )
