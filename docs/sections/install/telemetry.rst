Telemetry
---------

As an open source project, we collect usage statistics to inform development
priorities. Telemetry data will motivate projects such as adding features in
frequently-used parts of the CLI and adding more examples in the docs in
areas where users encounter more errors.

For example, we monitor the error rate of ``dagster execute pipeline``
invocations to help us ensure our programming model is intuitive to use and
to catch docs regressions.

We will not see or store solid definitions (including generated context) or
pipeline definitions (including modes and resources). We will not see or
store any data that is processed within solids and pipelines.

The telemetry-instrumented functions are:

.. literalinclude:: ../../../python_modules/dagster/dagster/core/telemetry.py
   :lines: 46-50
   :linenos:
   :caption: telemetry.py
   :language: python


To see the logs we send, inspect $DAGSTER_HOME/logs/ if $DAGSTER_HOME is set or
~/.dagster/logs/ after calling the instrumented functions above.

If you'd like to opt-out, you can add the following to ``$DAGSTER_HOME/dagster.yaml`` (creating
that file if necessary):

.. code-block:: yaml
   :caption: dagster.yaml

   telemetry:
     enabled: false
