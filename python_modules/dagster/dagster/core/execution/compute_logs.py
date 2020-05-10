from __future__ import print_function

import io
import os
import subprocess
import sys
import time
import warnings
from contextlib import contextmanager

from dagster.core.execution import poll_compute_logs, watch_orphans
from dagster.seven import IS_WINDOWS
from dagster.utils import ensure_file

WIN_PY36_COMPUTE_LOG_DISABLED_MSG = '''\u001b[33mWARNING: Compute log capture is disabled for the current environment. Set the environment variable `PYTHONLEGACYWINDOWSSTDIO` to enable.\n\u001b[0m'''


@contextmanager
def redirect_to_file(stream, filepath):
    with open(filepath, 'a+', buffering=1) as file_stream:
        with redirect_stream(file_stream, stream):
            yield


@contextmanager
def mirror_stream_to_file(stream, filepath):
    ensure_file(filepath)
    with tail_to_stream(filepath, stream):
        with redirect_to_file(stream, filepath):
            yield


def should_disable_io_stream_redirect():
    # See https://stackoverflow.com/a/52377087
    return (
        os.name == 'nt'
        and sys.version_info.major == 3
        and sys.version_info.minor >= 6
        and not os.environ.get('PYTHONLEGACYWINDOWSSTDIO')
    )


def warn_if_compute_logs_disabled():
    if should_disable_io_stream_redirect():
        warnings.warn(WIN_PY36_COMPUTE_LOG_DISABLED_MSG)


@contextmanager
def redirect_stream(to_stream=os.devnull, from_stream=sys.stdout):
    # swap the file descriptors to capture system-level output in the process
    # From https://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python/22434262#22434262
    from_fd = _fileno(from_stream)
    to_fd = _fileno(to_stream)

    if not from_fd or not to_fd or should_disable_io_stream_redirect():
        yield
        return

    with os.fdopen(os.dup(from_fd), 'wb') as copied:
        from_stream.flush()
        try:
            os.dup2(_fileno(to_stream), from_fd)
        except ValueError:
            with open(to_stream, 'wb') as to_file:
                os.dup2(to_file.fileno(), from_fd)
        try:
            yield from_stream
        finally:
            from_stream.flush()
            to_stream.flush()
            os.dup2(copied.fileno(), from_fd)


@contextmanager
def tail_to_stream(path, stream):
    if IS_WINDOWS:
        with execute_windows_tail(path, stream):
            yield
    else:
        with execute_posix_tail(path, stream):
            yield


@contextmanager
def execute_windows_tail(path, stream):
    # Cannot use multiprocessing here because we already may be in a daemonized process
    # Instead, invoke a thin script to poll a file and dump output to stdout.  We pass the current
    # pid so that the poll process kills itself if it becomes orphaned
    poll_file = os.path.abspath(poll_compute_logs.__file__)
    stream = stream if _fileno(stream) else None
    tail_process = subprocess.Popen(
        [sys.executable, poll_file, path, str(os.getpid())], stdout=stream
    )

    try:
        yield
    finally:
        if tail_process:
            time.sleep(2 * poll_compute_logs.POLLING_INTERVAL)
            tail_process.terminate()


@contextmanager
def execute_posix_tail(path, stream):
    # open a subprocess to tail the file and print to stdout
    tail_cmd = 'tail -F -c +0 {}'.format(path).split(' ')
    stream = stream if _fileno(stream) else None
    tail_process = subprocess.Popen(tail_cmd, stdout=stream)

    # open a watcher process to check for the orphaning of the tail process (e.g. when the
    # current process is suddenly killed)
    watcher_file = os.path.abspath(watch_orphans.__file__)
    watcher_process = subprocess.Popen(
        [sys.executable, watcher_file, str(os.getpid()), str(tail_process.pid),]
    )

    try:
        yield
    finally:
        _clean_up_subprocess(tail_process)
        _clean_up_subprocess(watcher_process)


def _clean_up_subprocess(subprocess_obj):
    try:
        if subprocess_obj:
            subprocess_obj.terminate()
    except OSError:
        pass


def _fileno(stream):
    try:
        fd = getattr(stream, 'fileno', lambda: stream)()
    except io.UnsupportedOperation:
        # Test CLI runners will stub out stdout to a non-file stream, which will raise an
        # UnsupportedOperation if `fileno` is accessed.  We need to make sure we do not error out,
        # or tests will fail
        return None

    if isinstance(fd, int):
        return fd

    return None
