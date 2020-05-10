import re

import pytest

from dagster import DagsterInvalidDefinitionError, Dict, List, Noneable, Optional, solid


def test_invalid_optional_in_config():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            'You have passed an instance of DagsterType Optional.Int to the config system'
        ),
    ):

        @solid(config=Optional[int])
        def _solid(_):
            pass


def test_invalid_dict_call():
    # prior to 0.7.0 dicts in config contexts were callable
    with pytest.raises(TypeError, match=re.escape("'DagsterDictApi' object is not callable")):

        @solid(config=Dict({'foo': int}))  # pylint: disable=not-callable
        def _solid(_):
            pass


def test_list_in_config():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            'Cannot use List in the context of config. Please use a python '
            'list (e.g. [int]) or dagster.Array (e.g. Array(int)) instead.'
        ),
    ):

        @solid(config=List[int])
        def _solid(_):
            pass


def test_invalid_list_element():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            'Invalid type: dagster_type must be DagsterType, '
            'a python scalar, or a python type that has been marked usable as '
            'a dagster type via @usable_dagster_type or '
            'make_python_type_usable_as_dagster_type:'
        ),
    ):
        _ = List[Noneable(int)]
