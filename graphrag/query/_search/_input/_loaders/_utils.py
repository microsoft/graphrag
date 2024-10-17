# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

import numpy as np
import pandas as pd


def to_str(data: pd.Series, column_name: typing.Optional[str]) -> str:
    """Convert and validate a value to a string."""
    if column_name is None:
        raise ValueError("Column name is None")

    if column_name in data:
        return str(data[column_name])
    raise ValueError(f"Column {column_name} not found in data")


def to_optional_str(data: pd.Series, column_name: typing.Optional[str]) -> typing.Optional[str]:
    """Convert and validate a value to an optional string."""
    if column_name is None:
        raise ValueError("Column name is None")

    if column_name in data:
        value = data[column_name]
        if value is None:
            return None
        return str(data[column_name])
    raise ValueError(f"Column {column_name} not found in data")


def to_list(
    data: pd.Series, column_name: typing.Optional[str], item_type: typing.Optional[type] = None
) -> list:
    """Convert and validate a value to a list."""
    if column_name is None:
        raise ValueError("Column name is None")

    if column_name in data:
        value = data[column_name]
        if isinstance(value, np.ndarray):
            value = value.tolist()

        if not isinstance(value, list):
            raise ValueError(f"value is not a list: {value} ({type(value)})")

        if item_type is not None:
            for v in value:
                if not isinstance(v, item_type):
                    raise TypeError(f"list item has item that is not {item_type}: {v} ({type(v)})")
        return value

    raise ValueError(f"Column {column_name} not found in data")


def to_optional_list(
    data: pd.Series, column_name: typing.Optional[str], item_type: typing.Optional[type] = None
) -> typing.Optional[list]:
    """Convert and validate a value to an optional list."""
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]  # type: ignore
        if value is None:
            return None

        if isinstance(value, np.ndarray):
            value = value.tolist()

        if not isinstance(value, list):
            raise ValueError(f"value is not a list: {value} ({type(value)})")

        if item_type is not None:
            for v in value:
                if not isinstance(v, item_type):
                    raise TypeError(f"list item has item that is not {item_type}: {v} ({type(v)})")
        return value

    return None


def to_int(data: pd.Series, column_name: typing.Optional[str]) -> int:
    """Convert and validate a value to an int."""
    if column_name is None:
        raise ValueError("Column name is None")

    if column_name in data:
        value = data[column_name]
        if isinstance(value, float):
            value = int(value)
        if not isinstance(value, int):
            raise ValueError(f"value is not an int: {value} ({type(value)})")
    else:
        raise ValueError(f"Column {column_name} not found in data")

    return int(value)


def to_optional_int(data: pd.Series, column_name: typing.Optional[str]) -> typing.Optional[int]:
    """Convert and validate a value to an optional int."""
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]

        if value is None:
            return None

        if isinstance(value, float):
            value = int(value)
        if not isinstance(value, int):
            raise ValueError(f"value is not an int: {value} ({type(value)})")
    else:
        raise ValueError(f"Column {column_name} not found in data")

    return int(value)


def to_float(data: pd.Series, column_name: typing.Optional[str]) -> float:
    """Convert and validate a value to a float."""
    if column_name is None:
        raise ValueError("Column name is None")

    if column_name in data:
        value = data[column_name]
        if not isinstance(value, float):
            raise ValueError(f"value is not a float: {value} ({type(value)})")
    else:
        raise ValueError(f"Column {column_name} not found in data")

    return float(value)


def to_optional_float(data: pd.Series, column_name: typing.Optional[str]) -> typing.Optional[float]:
    """Convert and validate a value to an optional float."""
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]
        if value is None:
            return None
        if not isinstance(value, float):
            raise ValueError(f"value is not a float: {value} ({type(value)})")
    else:
        raise ValueError(f"Column {column_name} not found in data")

    return float(value)


def to_dict(
    data: pd.Series,
    column_name: typing.Optional[str],
    key_type: typing.Optional[type] = None,
    value_type: typing.Optional[type] = None,
) -> dict:
    """Convert and validate a value to a dict."""
    if column_name is None:
        raise ValueError("Column name is None")

    if column_name in data:
        value = data[column_name]
        if not isinstance(value, dict):
            raise ValueError(f"value is not a dict: {value} ({type(value)})")

        if key_type is not None:
            for v in value:
                if not isinstance(v, key_type):
                    raise TypeError(f"dict key has item that is not {key_type}: {v} ({type(v)})")

        if value_type is not None:
            for v in value.values():
                if not isinstance(v, value_type):
                    raise TypeError(f"dict value has item that is not {value_type}: {v} ({type(v)})")
        return value

    raise ValueError(f"Column {column_name} not found in data")


def to_optional_dict(
    data: pd.Series,
    column_name: typing.Optional[str],
    key_type: typing.Optional[type] = None,
    value_type: typing.Optional[type] = None,
) -> typing.Optional[dict]:
    """Convert and validate a value to an optional dict."""
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]
        if value is None:
            return None
        if not isinstance(value, dict):
            raise TypeError(f"value is not a dict: {value} ({type(value)})")

        if key_type is not None:
            for v in value:
                if not isinstance(v, key_type):
                    raise TypeError(f"dict key has item that is not {key_type}: {v} ({type(v)})")

        if value_type is not None:
            for v in value.values():
                if not isinstance(v, value_type):
                    raise TypeError(f"dict value has item that is not {value_type}: {v} ({type(v)})")

        return value

    raise ValueError(f"Column {column_name} not found in data")
