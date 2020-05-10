import os
import re

import pytest

from ..dagster_module import DagsterModule
from ..dagster_module_publisher import (
    DagsterModulePublisher,
    get_core_module_directories,
    get_library_module_directories,
    get_nightly_version,
)


def test_all_module_versions():
    dmp = DagsterModulePublisher()
    versions = dmp.all_module_versions
    for key in ['dagster', 'dagit', 'dagster-graphql']:
        assert key in versions
        assert '__version__' in versions[key]
        assert '__nightly__' in versions[key]


def test_check_directory_structure():
    dmp = DagsterModulePublisher()
    assert dmp.check_directory_structure() is None


def test_get_core_module_directories():
    module_dirs = get_core_module_directories()
    as_dict = {m.name: m for m in module_dirs}
    for expected in ['dagster', 'dagit', 'dagster-graphql']:
        assert expected in as_dict
        # expect path to be <some prefix>/python_modules/<expected>
        assert as_dict[expected].path.endswith(os.path.join('python_modules', expected))


def test_get_library_module_directories():
    module_dirs = get_library_module_directories()
    as_dict = {m.name: m for m in module_dirs}
    for expected in ['dagster-airflow', 'dagster-k8s']:
        assert expected in as_dict
        # expect path to be <some prefix>/python_modules/<expected>
        assert as_dict[expected].path.endswith(
            os.path.join('python_modules', 'libraries', expected)
        )


def test_bad_core_module(bad_core_module):  # pylint: disable=unused-argument
    dmp = DagsterModulePublisher()

    with pytest.raises(Exception) as exc_info:
        dmp.check_directory_structure()

    assert exc_info.match(
        re.compile(r'Found unexpected modules:.*bad_core_module', re.MULTILINE | re.DOTALL)
    )


def test_set_version_info():
    new_version = '100.100.0'
    new_nightly_version = get_nightly_version()
    dmp = DagsterModulePublisher()

    # Test setting both version and nightly
    version = dmp.set_version_info(new_version=new_version, dry_run=True)
    assert version == {'__version__': new_version, '__nightly__': new_nightly_version}

    # Test only setting nightly
    version = dmp.set_version_info(dry_run=True)
    dm = DagsterModule('dagster', is_library=False)
    existing_version = dm.get_version_info()['__version__']
    assert version == {'__version__': existing_version, '__nightly__': new_nightly_version}
