import pandas as pd
from dagster_pandas.constraints import (
    ColumnDTypeFnConstraint,
    ColumnDTypeInSetConstraint,
    ConstraintViolationException,
)
from dagster_pandas.validation import PandasColumn, validate_constraints

from dagster import (
    DagsterInvariantViolationError,
    DagsterType,
    EventMetadataEntry,
    Field,
    Materialization,
    Path,
    String,
    TypeCheck,
    check,
)
from dagster.config.field_utils import Selector
from dagster.core.types.config_schema import input_selector_schema, output_selector_schema

CONSTRAINT_BLACKLIST = {ColumnDTypeFnConstraint, ColumnDTypeInSetConstraint}


def dict_without_keys(ddict, *keys):
    return {key: value for key, value in ddict.items() if key not in set(keys)}


@output_selector_schema(
    Selector(
        {
            'csv': {'path': Path, 'sep': Field(String, is_required=False, default_value=','),},
            'parquet': {'path': Path},
            'table': {'path': Path},
        },
    )
)
def dataframe_output_schema(_context, file_type, file_options, pandas_df):
    check.str_param(file_type, 'file_type')
    check.dict_param(file_options, 'file_options')
    check.inst_param(pandas_df, 'pandas_df', pd.DataFrame)

    if file_type == 'csv':
        path = file_options['path']
        pandas_df.to_csv(path, index=False, **dict_without_keys(file_options, 'path'))
    elif file_type == 'parquet':
        pandas_df.to_parquet(file_options['path'])
    elif file_type == 'table':
        pandas_df.to_csv(file_options['path'], sep='\t', index=False)
    else:
        check.failed('Unsupported file_type {file_type}'.format(file_type=file_type))

    return Materialization.file(file_options['path'])


@input_selector_schema(
    Selector(
        {
            'csv': {'path': Path, 'sep': Field(String, is_required=False, default_value=','),},
            'parquet': {'path': Path},
            'table': {'path': Path},
        },
    )
)
def dataframe_input_schema(_context, file_type, file_options):
    check.str_param(file_type, 'file_type')
    check.dict_param(file_options, 'file_options')

    if file_type == 'csv':
        path = file_options['path']
        return pd.read_csv(path, **dict_without_keys(file_options, 'path'))
    elif file_type == 'parquet':
        return pd.read_parquet(file_options['path'])
    elif file_type == 'table':
        return pd.read_csv(file_options['path'], sep='\t')
    else:
        raise DagsterInvariantViolationError(
            'Unsupported file_type {file_type}'.format(file_type=file_type)
        )


def df_type_check(_, value):
    if not isinstance(value, pd.DataFrame):
        return TypeCheck(success=False)
    return TypeCheck(
        success=True,
        metadata_entries=[
            EventMetadataEntry.text(str(len(value)), 'row_count', 'Number of rows in DataFrame'),
            # string cast columns since they may be things like datetime
            EventMetadataEntry.json({'columns': list(map(str, value.columns))}, 'metadata'),
        ],
    )


DataFrame = DagsterType(
    name='PandasDataFrame',
    description='''Two-dimensional size-mutable, potentially heterogeneous
    tabular data structure with labeled axes (rows and columns).
    See http://pandas.pydata.org/''',
    input_hydration_config=dataframe_input_schema,
    output_materialization_config=dataframe_output_schema,
    type_check_fn=df_type_check,
)


def _construct_constraint_list(constraints):
    def add_bullet(constraint_list, constraint_description):
        return constraint_list + "+ {constraint_description}\n".format(
            constraint_description=constraint_description
        )

    constraint_list = ""
    for constraint in constraints:
        if constraint.__class__ not in CONSTRAINT_BLACKLIST:
            constraint_list = add_bullet(constraint_list, constraint.markdown_description)
    return constraint_list


def _build_column_header(column_name, constraints):
    header = '**{column_name}**'.format(column_name=column_name)
    for constraint in constraints:
        if isinstance(constraint, ColumnDTypeInSetConstraint):
            dtypes_tuple = tuple(constraint.expected_dtype_set)
            return header + ": `{expected_dtypes}`".format(
                expected_dtypes=dtypes_tuple if len(dtypes_tuple) > 1 else dtypes_tuple[0]
            )
        elif isinstance(constraint, ColumnDTypeFnConstraint):
            return header + ": Validator `{expected_dtype_fn}`".format(
                expected_dtype_fn=constraint.type_fn.__name__
            )
    return header


def create_dagster_pandas_dataframe_description(description, columns):
    title = "\n".join([description, '### Columns', ''])
    buildme = title
    for column in columns:
        buildme += "{}\n{}\n".format(
            _build_column_header(column.name, column.constraints),
            _construct_constraint_list(column.constraints),
        )
    return buildme


def create_dagster_pandas_dataframe_type(
    name,
    description=None,
    columns=None,
    event_metadata_fn=None,
    dataframe_constraints=None,
    input_hydration_config=None,
    output_materialization_config=None,
):
    """
    Constructs a custom pandas dataframe dagster type.

    Args:
        name (str): Name of the dagster pandas type.
        description (Optional[str]): A markdown-formatted string, displayed in tooling.
        columns (Optional[List[PandasColumn]]): A list of :py:class:`~dagster.PandasColumn` objects
            which express dataframe column schemas and constraints.
        event_metadata_fn (Optional[func]): A callable which takes your dataframe and returns a list of EventMetadata
            which allow you to express things like summary statistics during runtime.
        dataframe_constraints (Optional[List[DataFrameConstraint]]): A list of objects that inherit from
            :py:class:`~dagster.DataFrameConstraint`. This allows you to express dataframe-level constraints.
        input_hydration_config (Optional[InputHydrationConfig]): An instance of a class that
            inherits from :py:class:`~dagster.InputHydrationConfig`. If None, we will default
            to using the `dataframe_input_schema` input_hydration_config.
        output_materialization_config (Optional[OutputMaterializationConfig]): An instance of a class
            that inherits from :py:class:`~dagster.OutputMaterializationConfig`. If None, we will
            default to using the `dataframe_output_schema` output_materialization_config.
    """
    # We allow for the plugging in of input_hydration_config/output_materialization_configs so that
    # Users can hydrate and persist their custom dataframes via configuration their own way if the default
    # configs don't suffice. This is purely optional.
    check.str_param(name, 'name')
    event_metadata_fn = check.opt_callable_param(event_metadata_fn, 'event_metadata_fn')
    description = create_dagster_pandas_dataframe_description(
        check.opt_str_param(description, 'description', default=''),
        check.opt_list_param(columns, 'columns', of_type=PandasColumn),
    )

    def _dagster_type_check(_, value):
        if not isinstance(value, pd.DataFrame):
            return TypeCheck(
                success=False,
                description='Must be a pandas.DataFrame. Got value of type. {type_name}'.format(
                    type_name=type(value).__name__
                ),
            )

        try:
            validate_constraints(
                value, pandas_columns=columns, dataframe_constraints=dataframe_constraints
            )
        except ConstraintViolationException as e:
            return TypeCheck(success=False, description=str(e))

        return TypeCheck(
            success=True,
            metadata_entries=_execute_summary_stats(name, value, event_metadata_fn)
            if event_metadata_fn
            else None,
        )

    return DagsterType(
        name=name,
        type_check_fn=_dagster_type_check,
        input_hydration_config=input_hydration_config
        if input_hydration_config
        else dataframe_input_schema,
        output_materialization_config=output_materialization_config
        if output_materialization_config
        else dataframe_output_schema,
        description=description,
    )


def _execute_summary_stats(type_name, value, event_metadata_fn):
    if not event_metadata_fn:
        return []

    metadata_entries = event_metadata_fn(value)

    if not (
        isinstance(metadata_entries, list)
        and all(isinstance(item, EventMetadataEntry) for item in metadata_entries)
    ):
        raise DagsterInvariantViolationError(
            (
                'The return value of the user-defined summary_statistics function '
                'for pandas data frame type {type_name} returned {value}. '
                'This function must return List[EventMetadataEntry]'
            ).format(type_name=type_name, value=repr(metadata_entries))
        )

    return metadata_entries
