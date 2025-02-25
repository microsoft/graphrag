# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Data load utils."""

from collections.abc import Mapping
from typing import Any

import numpy as np


def _get_value(
    data: Mapping[str, Any], column_name: str | None, required: bool = True
) -> Any:
    """
    Retrieve a column value from data.

    If `required` is True, raises a ValueError when:
      - column_name is None, or
      - column_name is not in data.

    For optional columns (required=False), returns None if column_name is None.
    """
    if column_name is None:
        if required:
            msg = "Column name is None"
            raise ValueError(msg)
        return None
    if column_name in data:
        return data[column_name]
    if required:
        msg = f"Column [{column_name}] not found in data"
        raise ValueError(msg)
    return None


def to_str(data: Mapping[str, Any], column_name: str | None) -> str:
    """Convert and validate a value to a string."""
    value = _get_value(data, column_name, required=True)
    return str(value)


def to_optional_str(data: Mapping[str, Any], column_name: str | None) -> str | None:
    """Convert and validate a value to an optional string."""
    value = _get_value(data, column_name, required=True)
    return None if value is None else str(value)


def to_list(
    data: Mapping[str, Any], column_name: str | None, item_type: type | None = None
) -> list:
    """Convert and validate a value to a list."""
    value = _get_value(data, column_name, required=True)
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if not isinstance(value, list):
        msg = f"value is not a list: {value} ({type(value)})"
        raise TypeError(msg)
    if item_type is not None:
        for v in value:
            if not isinstance(v, item_type):
                msg = f"list item is not [{item_type}]: {v} ({type(v)})"
                raise TypeError(msg)
    return value


def to_optional_list(
    data: Mapping[str, Any], column_name: str | None, item_type: type | None = None
) -> list | None:
    """Convert and validate a value to an optional list."""
    if column_name is None or column_name not in data:
        return None
    value = data[column_name]
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        msg = f"value is not a list: {value} ({type(value)})"
        raise TypeError(msg)
    if item_type is not None:
        for v in value:
            if not isinstance(v, item_type):
                msg = f"list item is not [{item_type}]: {v} ({type(v)})"
                raise TypeError(msg)
    return value


def to_int(data: Mapping[str, Any], column_name: str | None) -> int:
    """Convert and validate a value to an int."""
    value = _get_value(data, column_name, required=True)
    if isinstance(value, float):
        value = int(value)
    if not isinstance(value, int):
        msg = f"value is not an int: {value} ({type(value)})"
        raise TypeError(msg)
    return int(value)


def to_optional_int(data: Mapping[str, Any], column_name: str | None) -> int | None:
    """Convert and validate a value to an optional int."""
    if column_name is None or column_name not in data:
        return None
    value = data[column_name]
    if value is None:
        return None
    if isinstance(value, float):
        value = int(value)
    if not isinstance(value, int):
        msg = f"value is not an int: {value} ({type(value)})"
        raise TypeError(msg)
    return int(value)


def to_float(data: Mapping[str, Any], column_name: str | None) -> float:
    """Convert and validate a value to a float."""
    value = _get_value(data, column_name, required=True)
    if not isinstance(value, float):
        msg = f"value is not a float: {value} ({type(value)})"
        raise TypeError(msg)
    return float(value)


def to_optional_float(data: Mapping[str, Any], column_name: str | None) -> float | None:
    """Convert and validate a value to an optional float."""
    if column_name is None or column_name not in data:
        return None
    value = data[column_name]
    if value is None:
        return None
    if not isinstance(value, float):
        return float(value)
    return float(value)


def to_dict(
    data: Mapping[str, Any],
    column_name: str | None,
    key_type: type | None = None,
    value_type: type | None = None,
) -> dict:
    """Convert and validate a value to a dict."""
    value = _get_value(data, column_name, required=True)
    if not isinstance(value, dict):
        msg = f"value is not a dict: {value} ({type(value)})"
        raise TypeError(msg)
    if key_type is not None:
        for k in value:
            if not isinstance(k, key_type):
                msg = f"dict key is not [{key_type}]: {k} ({type(k)})"
                raise TypeError(msg)
    if value_type is not None:
        for v in value.values():
            if not isinstance(v, value_type):
                msg = f"dict value is not [{value_type}]: {v} ({type(v)})"
                raise TypeError(msg)
    return value


def to_optional_dict(
    data: Mapping[str, Any],
    column_name: str | None,
    key_type: type | None = None,
    value_type: type | None = None,
) -> dict | None:
    """Convert and validate a value to an optional dict."""
    if column_name is None or column_name not in data:
        return None
    value = data[column_name]
    if value is None:
        return None
    if not isinstance(value, dict):
        msg = f"value is not a dict: {value} ({type(value)})"
        raise TypeError(msg)
    if key_type is not None:
        for k in value:
            if not isinstance(k, key_type):
                msg = f"dict key is not [{key_type}]: {k} ({type(k)})"
                raise TypeError(msg)
    if value_type is not None:
        for v in value.values():
            if not isinstance(v, value_type):
                msg = f"dict value is not [{value_type}]: {v} ({type(v)})"
                raise TypeError(msg)
    return value
