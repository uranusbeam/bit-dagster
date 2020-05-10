import sys
from collections import namedtuple
from enum import Enum

import pytest

from dagster.check import CheckError, ParameterCheckError
from dagster.serdes import (
    SerdesClassUsageError,
    _deserialize_json_to_dagster_namedtuple,
    _pack_value,
    _serialize_dagster_namedtuple,
    _unpack_value,
    _whitelist_for_serdes,
    deserialize_json_to_dagster_namedtuple,
    deserialize_value,
)


def test_deserialize_value_ok():
    unpacked_tuple = deserialize_value('{"foo": "bar"}')
    assert unpacked_tuple
    assert unpacked_tuple['foo'] == 'bar'


def test_deserialize_json_to_dagster_namedtuple_non_namedtuple():
    with pytest.raises(CheckError):
        deserialize_json_to_dagster_namedtuple('{"foo": "bar"}')


@pytest.mark.parametrize('bad_obj', [1, None, False])
def test_deserialize_json_to_dagster_namedtuple_invalid_types(bad_obj):
    with pytest.raises(ParameterCheckError):
        deserialize_json_to_dagster_namedtuple(bad_obj)


def test_forward_compat_serdes_new_field_with_default():
    _TEST_TUPLE_MAP = {}
    _TEST_ENUM_MAP = {}

    @_whitelist_for_serdes(tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP)
    class Quux(namedtuple('_Quux', 'foo bar')):
        def __new__(cls, foo, bar):
            return super(Quux, cls).__new__(cls, foo, bar)  # pylint: disable=bad-super-call

    assert 'Quux' in _TEST_TUPLE_MAP
    assert _TEST_TUPLE_MAP['Quux'] == Quux

    quux = Quux('zip', 'zow')

    serialized = _serialize_dagster_namedtuple(
        quux, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )

    @_whitelist_for_serdes(
        tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )  # pylint: disable=function-redefined
    class Quux(namedtuple('_Quux', 'foo bar baz')):  # pylint: disable=bad-super-call
        def __new__(cls, foo, bar, baz=None):
            return super(Quux, cls).__new__(cls, foo, bar, baz=baz)

    assert 'Quux' in _TEST_TUPLE_MAP
    assert _TEST_TUPLE_MAP['Quux'] == Quux

    deserialized = _deserialize_json_to_dagster_namedtuple(
        serialized, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )

    assert deserialized != quux
    assert deserialized.foo == quux.foo
    assert deserialized.bar == quux.bar
    assert deserialized.baz is None


def test_forward_compat_serdes_new_enum_field():
    _TEST_TUPLE_MAP = {}
    _TEST_ENUM_MAP = {}

    @_whitelist_for_serdes(tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP)
    class Corge(Enum):
        FOO = 1
        BAR = 2

    assert 'Corge' in _TEST_ENUM_MAP

    corge = Corge.FOO

    packed = _pack_value(corge, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP)

    @_whitelist_for_serdes(
        tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )  # pylint: disable=function-redefined
    class Corge(Enum):
        FOO = 1
        BAR = 2
        BAZ = 3

    unpacked = _unpack_value(packed, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP)

    assert unpacked != corge
    assert unpacked.name == corge.name
    assert unpacked.value == corge.value


# This behavior isn't possible on 2.7 because of `inspect` limitations
@pytest.mark.skipif(sys.version_info < (3,), reason="This behavior isn't available on 2.7")
def test_backward_compat_serdes():
    _TEST_TUPLE_MAP = {}
    _TEST_ENUM_MAP = {}

    @_whitelist_for_serdes(tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP)
    class Quux(namedtuple('_Quux', 'foo bar baz')):
        def __new__(cls, foo, bar, baz):
            return super(Quux, cls).__new__(cls, foo, bar, baz)  # pylint: disable=bad-super-call

    quux = Quux('zip', 'zow', 'whoopie')

    serialized = _serialize_dagster_namedtuple(
        quux, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )

    @_whitelist_for_serdes(
        tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )  # pylint: disable=function-redefined
    class Quux(namedtuple('_Quux', 'foo bar')):  # pylint: disable=bad-super-call
        def __new__(cls, foo, bar):
            return super(Quux, cls).__new__(cls, foo, bar)

    deserialized = _deserialize_json_to_dagster_namedtuple(
        serialized, tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_ENUM_MAP
    )

    assert deserialized != quux
    assert deserialized.foo == quux.foo
    assert deserialized.bar == quux.bar
    assert not hasattr(deserialized, 'baz')


def serdes_test_class(klass):
    _TEST_TUPLE_MAP = {}
    _TEST_ENUM_MAP = {}

    return _whitelist_for_serdes(tuple_map=_TEST_TUPLE_MAP, enum_map=_TEST_TUPLE_MAP)(klass)


@pytest.mark.skipif(
    sys.version_info.major < 3, reason='Serdes declaration time checks python 3 only'
)
def test_wrong_first_arg():
    with pytest.raises(SerdesClassUsageError) as exc_info:

        @serdes_test_class
        class NotCls(namedtuple('NotCls', 'field_one field_two')):
            def __new__(not_cls, field_two, field_one):
                super(NotCls, not_cls).__new__(field_one, field_two)

    assert (
        str(exc_info.value)
        == 'For namedtuple NotCls: First parameter must be _cls or cls. Got "not_cls".'
    )


@pytest.mark.skipif(
    sys.version_info.major < 3, reason='Serdes declaration time checks python 3 only'
)
def test_incorrect_order():
    with pytest.raises(SerdesClassUsageError) as exc_info:

        @serdes_test_class
        class WrongOrder(namedtuple('WrongOrder', 'field_one field_two')):
            def __new__(cls, field_two, field_one):
                super(WrongOrder, cls).__new__(field_one, field_two)

    assert str(exc_info.value) == (
        'For namedtuple WrongOrder: '
        'Params to __new__ must match the order of field declaration '
        'in the namedtuple. Declared field number 1 in the namedtuple '
        'is "field_one". Parameter 1 in __new__ method is "field_two".'
    )


@pytest.mark.skipif(
    sys.version_info.major < 3, reason='Serdes declaration time checks python 3 only'
)
def test_missing_one_parameter():
    with pytest.raises(SerdesClassUsageError) as exc_info:

        @serdes_test_class
        class MissingFieldInNew(namedtuple('MissingFieldInNew', 'field_one field_two field_three')):
            def __new__(cls, field_one, field_two):
                super(MissingFieldInNew, cls).__new__(field_one, field_two, None)

    assert str(exc_info.value) == (
        "For namedtuple MissingFieldInNew: "
        "Missing parameters to __new__. You have declared fields in "
        "the named tuple that are not present as parameters to the "
        "to the __new__ method. In order for both serdes serialization "
        "and pickling to work, these must match. Missing: ['field_three']"
    )


@pytest.mark.skipif(
    sys.version_info.major < 3, reason='Serdes declaration time checks python 3 only'
)
def test_missing_many_parameters():
    with pytest.raises(SerdesClassUsageError) as exc_info:

        @serdes_test_class
        class MissingFieldsInNew(
            namedtuple('MissingFieldsInNew', 'field_one field_two field_three, field_four')
        ):
            def __new__(cls, field_one, field_two):
                super(MissingFieldsInNew, cls).__new__(field_one, field_two, None, None)

    assert str(exc_info.value) == (
        "For namedtuple MissingFieldsInNew: "
        "Missing parameters to __new__. You have declared fields in "
        "the named tuple that are not present as parameters to the "
        "to the __new__ method. In order for both serdes serialization "
        "and pickling to work, these must match. Missing: ['field_three', 'field_four']"
    )


@pytest.mark.skipif(
    sys.version_info.major < 3, reason='Serdes declaration time checks python 3 only'
)
def test_extra_parameters_must_have_defaults():
    with pytest.raises(SerdesClassUsageError) as exc_info:

        @serdes_test_class
        class OldFieldsWithoutDefaults(
            namedtuple('OldFieldsWithoutDefaults', 'field_three field_four')
        ):
            # pylint:disable=unused-argument
            def __new__(
                cls,
                field_three,
                field_four,
                # Graveyard Below
                field_one,
                field_two,
            ):
                super(OldFieldsWithoutDefaults, cls).__new__(field_three, field_four)

    assert str(exc_info.value) == (
        'For namedtuple OldFieldsWithoutDefaults: '
        'Parameter "field_one" is a parameter to the __new__ '
        'method but is not a field in this namedtuple. '
        'The only reason why this should exist is that '
        'it is a field that used to exist (we refer to '
        'this as the graveyard) but no longer does. However '
        'it might exist in historical storage. This parameter '
        'existing ensures that serdes continues to work. However '
        'these must come at the end and have a default value for pickling to work.'
    )


@pytest.mark.skipif(
    sys.version_info.major < 3, reason='Serdes declaration time checks python 3 only'
)
def test_extra_parameters_have_working_defaults():
    @serdes_test_class
    class OldFieldsWithDefaults(namedtuple('OldFieldsWithDefaults', 'field_three field_four')):
        # pylint:disable=unused-argument
        def __new__(
            cls,
            field_three,
            field_four,
            # Graveyard Below
            none_field=None,
            falsey_field=0,
            another_falsey_field='',
            value_field='klsjkfjd',
        ):
            super(OldFieldsWithDefaults, cls).__new__(field_three, field_four)
