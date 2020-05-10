Libraries
---------

Dagster includes a number of non-core libraries that provide integrations
and additional functionality:

  `Airflow <../../../api/apidocs/libraries/dagster_airflow.html>`_ (``dagster_airflow``)
    Tools for compiling Dagster pipelines to Airflow DAGs.
  `AWS <../../../api/apidocs/libraries/dagster_aws.html>`_ (``dagster_aws``)
    Tools for working with AWS, including using S3 for intermediates storage.
  `Bash <../../../api/apidocs/libraries/dagster_bash.html>`_ (``dagster_bash``)
    Provides solid factories for creating bash script solids.
  `Celery <../../../api/apidocs/libraries/dagster_celery.html>`_ (``dagster_celery``)
    Provides an executor built on top of the popular
    `Celery task queue <http:/www.celeryproject.org/>`_.
  `Cron <../../../api/apidocs/libraries/dagster_cron.html>`_ (``dagster_cron``)
    Provides a simple scheduler implementation built on system cron.
  `Dask <../../../api/apidocs/libraries/dagster_dask.html>`_ (``dagster_dask``)
    Provides an executor built on top of
    `dask.distributed <https:/distributed.dask.org/en/latest/>`_.
  `GCP <../../../api/apidocs/libraries/dagster_gcp.html>`_ (``dagster_gcp``)
    Tools for working with GCP, including using GCS for intermediates storage.
  `Jupyter <../../../api/apidocs/libraries/dagstermill.html>`_ (``dagstermill``)
    Wraps Jupyter notebooks as solids for integrated execution within pipeline
    runs.
  `Kubernetes <../../../api/apidocs/libraries/dagster_k8s.html>`_ (``dagster_k8s``)
    Tools for deploying Dagster to Kubernetes.
  `Postgres <../../../api/apidocs/libraries/dagster_postgres.html>`_ (``dagster_postgres``)
    Includes implementations of run and event log storage built on Postgres.

.. toctree::
  :maxdepth: 2
  :name: Libraries API Reference
  :hidden:

  Airflow (dagster_airflow) <dagster_airflow>
  AWS (dagster_aws) <dagster_aws>
  Bash (dagster_bash) <dagster_bash>
  Celery (dagster_celery) <dagster_celery>
  Cron (dagster_cron) <dagster_cron>
  Dask (dagster_dask) <dagster_dask>
  GCP (dagster_gcp) <dagster_gcp>
  Jupyter (dagstermill) <dagstermill>
  Kubernetes (dagster_k8s) <dagster_k8s>
  Postgres dagster_postgres <dagster_postgres>
