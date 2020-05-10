import logging
import time
from enum import Enum

import kubernetes
import six

from dagster import check

DEFAULT_WAIT_TIMEOUT = 600.0  # 10 minutes
DEFAULT_WAIT_BETWEEN_ATTEMPTS = 1.0  # 1 second
DEFAULT_JOB_POD_COUNT = 1  # expect job:pod to be 1:1 by default


class DagsterK8sError(Exception):
    pass


class WaitForPodState(Enum):
    Ready = 'READY'
    Terminated = 'TERMINATED'


def retrieve_pod_logs(pod_name, namespace):
    '''Retrieves the raw pod logs for the pod named `pod_name` from Kubernetes.

    Args:
        pod_name (str): The name of the pod from which to retrieve logs.
        namespace (str): The namespace of the pod.

    Returns:
        str: The raw logs retrieved from the pod.
    '''
    check.str_param(pod_name, 'pod_name')
    check.str_param(namespace, 'namespace')

    # We set _preload_content to False here to prevent the k8 python api from processing the response.
    # If the logs happen to be JSON - it will parse in to a dict and then coerce back to a str leaving
    # us with invalid JSON as the quotes have been switched to '
    #
    # https://github.com/kubernetes-client/python/issues/811
    return six.ensure_str(
        kubernetes.client.CoreV1Api()
        .read_namespaced_pod_log(name=pod_name, namespace=namespace, _preload_content=False)
        .data
    )


def get_pod_names_in_job(job_name, namespace):
    '''Get the names of pods launched by the job ``job_name``.

    Args:
        job_name (str): Name of the job to inspect.
        namespace (str): Namespace in which the job is located.

    Returns:
        List[str]: List of all pod names that have been launched by the job ``job_name``.
    '''
    check.str_param(job_name, 'job_name')
    check.str_param(namespace, 'namespace')

    kube_api = kubernetes.client.CoreV1Api()
    pods = kube_api.list_namespaced_pod(
        namespace=namespace, label_selector='job-name={}'.format(job_name)
    ).items
    return [p.metadata.name for p in pods]


def wait_for_job_success(
    job_name,
    namespace,
    wait_timeout=DEFAULT_WAIT_TIMEOUT,
    wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
    num_pods_to_wait_for=DEFAULT_JOB_POD_COUNT,
):
    '''Poll a job for successful completion.

    Args:
        job_name (str): Name of the job to wait for.
        namespace (str): Namespace in which the job is located.
        wait_timeout (numeric, optional): Timeout after which to give up and raise exception.
            Defaults to DEFAULT_WAIT_TIMEOUT.
        wait_time_between_attempts (numeric, optional): Wait time between polling attempts. Defaults
            to DEFAULT_WAIT_BETWEEN_ATTEMPTS.

    Raises:
        DagsterK8sError: Raised when wait_timeout is exceeded or an error is encountered.
    '''
    check.str_param(job_name, 'job_name')
    check.str_param(namespace, 'namespace')
    check.numeric_param(wait_timeout, 'wait_timeout')
    check.numeric_param(wait_time_between_attempts, 'wait_time_between_attempts')
    check.int_param(num_pods_to_wait_for, 'num_pods_to_wait_for')

    api = kubernetes.client.BatchV1Api()

    job = None

    start = time.time()

    # Ensure we found the job that we launched
    while not job:
        if time.time() - start > wait_timeout:
            raise DagsterK8sError('Timed out while waiting for job to launch')

        jobs = api.list_namespaced_job(namespace=namespace)
        job = next((j for j in jobs.items if j.metadata.name == job_name), None)

        logging.info('Job "%s" not yet launched, waiting' % job_name)
        time.sleep(wait_time_between_attempts)

    # Wait for job completed status
    while True:
        if time.time() - start > wait_timeout:
            raise DagsterK8sError('Timed out while waiting for job to complete')

        # See: https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.11/#jobstatus-v1-batch
        status = api.read_namespaced_job_status(job_name, namespace=namespace).status

        if status.failed and status.failed > 0:
            raise DagsterK8sError('Encountered failed job pods with status: %s' % str(status))

        # done waiting for pod completion
        if status.succeeded == num_pods_to_wait_for:
            break

        time.sleep(wait_time_between_attempts)


def wait_for_pod(
    pod_name,
    namespace,
    wait_for_state=WaitForPodState.Ready,
    wait_timeout=DEFAULT_WAIT_TIMEOUT,
    wait_time_between_attempts=DEFAULT_WAIT_BETWEEN_ATTEMPTS,
):
    '''Wait for a pod to launch and be running, or wait for termination (useful for job pods).

    Args:
        pod_name (str): Name of the pod to wait for.
        namespace (str): Namespace in which the pod is located.
        wait_for_state (WaitForPodState, optional): Whether to wait for pod readiness or
            termination. Defaults to waiting for readiness.
        wait_timeout (numeric, optional): Timeout after which to give up and raise exception.
            Defaults to DEFAULT_WAIT_TIMEOUT.
        wait_time_between_attempts (numeric, optional): Wait time between polling attempts. Defaults
            to DEFAULT_WAIT_BETWEEN_ATTEMPTS.

    Raises:
        DagsterK8sError: Raised when wait_timeout is exceeded or an error is encountered
    '''
    check.str_param(pod_name, 'pod_name')
    check.str_param(namespace, 'namespace')
    check.inst_param(wait_for_state, 'wait_for_state', WaitForPodState)
    check.numeric_param(wait_timeout, 'wait_timeout')
    check.numeric_param(wait_time_between_attempts, 'wait_time_between_attempts')

    logging.info('Waiting for pod %s' % pod_name)

    start = time.time()

    while True:
        pods = (
            kubernetes.client.CoreV1Api()
            .list_namespaced_pod(namespace=namespace, field_selector='metadata.name=%s' % pod_name)
            .items
        )
        pod = pods[0] if pods else None

        if time.time() - start > wait_timeout:
            raise DagsterK8sError(
                'Timed out while waiting for pod to become ready with pod info: %s' % str(pod)
            )

        if pod is None:
            logging.info('Waiting for pod "%s" to launch...' % pod_name)
            time.sleep(wait_time_between_attempts)
            continue

        if not pod.status.container_statuses:
            logging.info('Waiting for pod container status to be set by kubernetes...')
            time.sleep(wait_time_between_attempts)
            continue

        # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstatus-v1-core
        container_status = pod.status.container_statuses[0]

        # State checks below, see:
        # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstate-v1-core
        state = container_status.state

        if state.running is not None:
            if wait_for_state == WaitForPodState.Ready:
                # ready is boolean field of container status
                ready = container_status.ready
                if not ready:
                    logging.info('Waiting for pod "%s" to become ready...' % pod_name)
                    time.sleep(wait_time_between_attempts)
                    continue
                else:
                    logging.info('Pod "%s" is ready, done waiting' % pod_name)
                    break
            elif wait_for_state == WaitForPodState.Terminated:
                time.sleep(wait_time_between_attempts)
                continue
            else:
                raise DagsterK8sError('Unknown wait for state %s' % str(wait_for_state.value))
            break

        elif state.waiting is not None:
            # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstatewaiting-v1-core
            if state.waiting.reason == 'PodInitializing':
                logging.info('Waiting for pod "%s" to initialize...' % pod_name)
                time.sleep(wait_time_between_attempts)
                continue
            elif state.waiting.reason == 'ContainerCreating':
                logging.info('Waiting for container creation...')
                time.sleep(wait_time_between_attempts)
                continue
            elif state.waiting.reason in [
                'ErrImagePull',
                'ImagePullBackOff',
                'CrashLoopBackOff',
                'RunContainerError',
            ]:
                raise DagsterK8sError('Failed: %s' % state.waiting.message)
            else:
                raise DagsterK8sError('Unknown issue: %s' % state.waiting)

        # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#containerstateterminated-v1-core
        elif state.terminated is not None:
            if not state.terminated.exit_code == 0:
                raw_logs = retrieve_pod_logs(pod_name, namespace)
                raise DagsterK8sError(
                    'Pod did not exit successfully. Failed with message: %s and pod logs: %s'
                    % (state.terminated.message, str(raw_logs))
                )
            break

        else:
            raise DagsterK8sError('Should not get here, unknown pod state')
