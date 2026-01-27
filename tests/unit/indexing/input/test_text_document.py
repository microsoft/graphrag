# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import pytest
from graphrag_input import get_property


def test_get_property_single_level():
    data = {"foo": "bar"}
    assert get_property(data, "foo") == "bar"


def test_get_property_two_levels():
    data = {"foo": {"bar": "baz"}}
    assert get_property(data, "foo.bar") == "baz"


def test_get_property_three_levels():
    data = {"a": {"b": {"c": "value"}}}
    assert get_property(data, "a.b.c") == "value"


def test_get_property_returns_dict():
    data = {"foo": {"bar": {"baz": "qux"}}}
    result = get_property(data, "foo.bar")
    assert result == {"baz": "qux"}


def test_get_property_missing_key_raises():
    data = {"foo": "bar"}
    with pytest.raises(KeyError):
        get_property(data, "missing")


def test_get_property_missing_nested_key_raises():
    data = {"foo": {"bar": "baz"}}
    with pytest.raises(KeyError):
        get_property(data, "foo.missing")


def test_get_property_non_dict_intermediate_raises():
    data = {"foo": "bar"}
    with pytest.raises(KeyError):
        get_property(data, "foo.bar")


def test_get_property_empty_dict_raises():
    data = {}
    with pytest.raises(KeyError):
        get_property(data, "foo")


def test_get_property_with_none_value():
    data = {"foo": None}
    assert get_property(data, "foo") is None


def test_get_property_with_list_value():
    data = {"foo": [1, 2, 3]}
    assert get_property(data, "foo") == [1, 2, 3]


def test_get_property_list_intermediate_raises():
    data = {"foo": [{"bar": "baz"}]}
    with pytest.raises(KeyError):
        get_property(data, "foo.bar")


def test_get_property_numeric_value():
    data = {"count": 42}
    assert get_property(data, "count") == 42


def test_get_property_boolean_value():
    data = {"enabled": True}
    assert get_property(data, "enabled") is True
