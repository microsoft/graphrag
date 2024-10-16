# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Data load utils."""

import numpy as np
import pandas as pd


def to_str(data: pd.Series, column_name: str | None) -> str:
    """Convert and validate a value to a string."""
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        return str(data[column_name])
    msg = f"Column {column_name} not found in data"
    raise ValueError(msg)


def to_optional_str(data: pd.Series, column_name: str | None) -> str | None:
    """Convert and validate a value to an optional string."""
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        value = data[column_name]
        if value is None:
            return None
        return str(data[column_name])
    msg = f"Column {column_name} not found in data"
    raise ValueError(msg)


def to_list(
    data: pd.Series, column_name: str | None, item_type: type | None = None
) -> list:
    """Convert and validate a value to a list."""
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        value = data[column_name]
        if isinstance(value, np.ndarray):
            value = value.tolist()

        if not isinstance(value, list):
            msg = f"value is not a list: {value} ({type(value)})"
            raise ValueError(msg)

        if item_type is not None:
            for v in value:
                if not isinstance(v, item_type):
                    msg = f"list item has item that is not {item_type}: {v} ({type(v)})"
                    raise TypeError(msg)
        return value

    msg = f"Column {column_name} not found in data"
    raise ValueError(msg)


def to_optional_list(
    data: pd.Series, column_name: str | None, item_type: type | None = None
) -> list | None:
    """Convert and validate a value to an optional list."""
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]  # type: ignore
        if value is None:
            return None

        if isinstance(value, np.ndarray):
            value = value.tolist()

        if isinstance(value, str):
            value = [value]

        if not isinstance(value, list):
            msg = f"value is not a list: {value} ({type(value)})"
            raise ValueError(msg)

        if item_type is not None:
            for v in value:
                if not isinstance(v, item_type):
                    msg = f"list item has item that is not {item_type}: {v} ({type(v)})"
                    raise TypeError(msg)
        return value

    return None


def to_int(data: pd.Series, column_name: str | None) -> int:
    """Convert and validate a value to an int."""
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        value = data[column_name]
        if isinstance(value, float):
            value = int(value)
        if not isinstance(value, int):
            msg = f"value is not an int: {value} ({type(value)})"
            raise ValueError(msg)
    else:
        msg = f"Column {column_name} not found in data"
        raise ValueError(msg)

    return int(value)


def to_optional_int(data: pd.Series, column_name: str | None) -> int | None:
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
            msg = f"value is not an int: {value} ({type(value)})"
            raise ValueError(msg)
    else:
        msg = f"Column {column_name} not found in data"
        raise ValueError(msg)

    return int(value)


def to_float(data: pd.Series, column_name: str | None) -> float:
    """Convert and validate a value to a float."""
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        value = data[column_name]
        if not isinstance(value, float):
            msg = f"value is not a float: {value} ({type(value)})"
            raise ValueError(msg)
    else:
        msg = f"Column {column_name} not found in data"
        raise ValueError(msg)

    return float(value)


def to_optional_float(data: pd.Series, column_name: str | None) -> float | None:
    """Convert and validate a value to an optional float."""
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]
        if value is None:
            return None
        if not isinstance(value, float):
            msg = f"value is not a float: {value} ({type(value)})"
            raise ValueError(msg)
    else:
        msg = f"Column {column_name} not found in data"
        raise ValueError(msg)

    return float(value)


def to_dict(
    data: pd.Series,
    column_name: str | None,
    key_type: type | None = None,
    value_type: type | None = None,
) -> dict:
    """Convert and validate a value to a dict."""
    if column_name is None:
        msg = "Column name is None"
        raise ValueError(msg)

    if column_name in data:
        value = data[column_name]
        if not isinstance(value, dict):
            msg = f"value is not a dict: {value} ({type(value)})"
            raise ValueError(msg)

        if key_type is not None:
            for v in value:
                if not isinstance(v, key_type):
                    msg = f"dict key has item that is not {key_type}: {v} ({type(v)})"
                    raise TypeError(msg)

        if value_type is not None:
            for v in value.values():
                if not isinstance(v, value_type):
                    msg = (
                        f"dict value has item that is not {value_type}: {v} ({type(v)})"
                    )
                    raise TypeError(msg)
        return value

    msg = f"Column {column_name} not found in data"
    raise ValueError(msg)


def to_optional_dict(
    data: pd.Series,
    column_name: str | None,
    key_type: type | None = None,
    value_type: type | None = None,
) -> dict | None:
    """Convert and validate a value to an optional dict."""
    if column_name is None:
        return None

    if column_name in data:
        value = data[column_name]
        if value is None:
            return None
        if not isinstance(value, dict):
            msg = f"value is not a dict: {value} ({type(value)})"
            raise TypeError(msg)

        if key_type is not None:
            for v in value:
                if not isinstance(v, key_type):
                    msg = f"dict key has item that is not {key_type}: {v} ({type(v)})"
                    raise TypeError(msg)

        if value_type is not None:
            for v in value.values():
                if not isinstance(v, value_type):
                    msg = (
                        f"dict value has item that is not {value_type}: {v} ({type(v)})"
                    )
                    raise TypeError(msg)

        return value

    msg = f"Column {column_name} not found in data"
    raise ValueError(msg)
