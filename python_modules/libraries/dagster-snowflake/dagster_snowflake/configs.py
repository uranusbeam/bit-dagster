from dagster import Bool, Field, Int, Path, String, StringSource


def define_snowflake_config():
    '''Snowflake configuration.

    See the Snowflake documentation for reference:
        https://docs.snowflake.net/manuals/user-guide/python-connector-api.html
    '''

    account = Field(
        StringSource,
        description='Your Snowflake account name. For more details, see  https://bit.ly/2FBL320.',
        is_required=False,
    )

    user = Field(StringSource, description='User login name.', is_required=True)

    password = Field(StringSource, description='User password.', is_required=True)

    database = Field(
        StringSource,
        description='''Name of the default database to use. After login, you can use USE DATABASE
         to change the database.''',
        is_required=False,
    )

    schema = Field(
        StringSource,
        description='''Name of the default schema to use. After login, you can use USE SCHEMA to
         change the schema.''',
        is_required=False,
    )

    role = Field(
        StringSource,
        description='''Name of the default role to use. After login, you can use USE ROLE to change
         the role.''',
        is_required=False,
    )

    warehouse = Field(
        StringSource,
        description='''Name of the default warehouse to use. After login, you can use USE WAREHOUSE
         to change the role.''',
        is_required=False,
    )

    autocommit = Field(
        Bool,
        description='''None by default, which honors the Snowflake parameter AUTOCOMMIT. Set to True
         or False to enable or disable autocommit mode in the session, respectively.''',
        is_required=False,
    )

    client_prefetch_threads = Field(
        Int,
        description='''Number of threads used to download the results sets (4 by default).
         Increasing the value improves fetch performance but requires more memory.''',
        is_required=False,
    )

    client_session_keep_alive = Field(
        String,
        description='''False by default. Set this to True to keep the session active indefinitely,
         even if there is no activity from the user. Make certain to call the close method to
         terminate the thread properly or the process may hang.''',
        is_required=False,
    )

    login_timeout = Field(
        Int,
        description='''Timeout in seconds for login. By default, 60 seconds. The login request gives
         up after the timeout length if the HTTP response is "success".''',
        is_required=False,
    )

    network_timeout = Field(
        Int,
        description='''Timeout in seconds for all other operations. By default, none/infinite. A
         general request gives up after the timeout length if the HTTP response is not "success"''',
        is_required=False,
    )

    ocsp_response_cache_filename = Field(
        Path,
        description='''URI for the OCSP response cache file.
         By default, the OCSP response cache file is created in the cache directory.''',
        is_required=False,
    )

    validate_default_parameters = Field(
        Bool,
        description='''False by default. Raise an exception if either one of specified database,
         schema or warehouse doesn't exists if True.''',
        is_required=False,
    )

    paramstyle = Field(
        # TODO should validate only against permissible values for this
        String,
        description='''pyformat by default for client side binding. Specify qmark or numeric to
        change bind variable formats for server side binding.''',
        is_required=False,
    )

    timezone = Field(
        String,
        description='''None by default, which honors the Snowflake parameter TIMEZONE. Set to a
         valid time zone (e.g. America/Los_Angeles) to set the session time zone.''',
        is_required=False,
    )

    return {
        'account': account,
        'user': user,
        'password': password,
        'database': database,
        'schema': schema,
        'role': role,
        'warehouse': warehouse,
        'autocommit': autocommit,
        'client_prefetch_threads': client_prefetch_threads,
        'client_session_keep_alive': client_session_keep_alive,
        'login_timeout': login_timeout,
        'network_timeout': network_timeout,
        'ocsp_response_cache_filename': ocsp_response_cache_filename,
        'validate_default_parameters': validate_default_parameters,
        'paramstyle': paramstyle,
        'timezone': timezone,
    }
