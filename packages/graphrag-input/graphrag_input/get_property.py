# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utility for retrieving properties from nested dictionaries."""

from typing import Any


def get_property(data: dict[str, Any], path: str) -> Any:
    """Retrieve a property from a dictionary using dot notation.

    Parameters
    ----------
    data : dict[str, Any]
        The dictionary to retrieve the property from.
    path : str
        A dot-separated string representing the path to the property (e.g., "foo.bar.baz").

    Returns
    -------
    Any
        The value at the specified path.

    Raises
    ------
    KeyError
        If the path does not exist in the dictionary.
    """
    keys = path.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            msg = f"Property '{path}' not found"
            raise KeyError(msg)
        current = current[key]
    return current
