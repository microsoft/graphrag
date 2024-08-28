# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Resolve timestamp variables in a path."""

import re
from pathlib import Path
from string import Template


def _resolve_timestamp_path_with_value(path: str | Path, timestamp_value: str) -> Path:
    """Resolve the timestamp in the path with the given timestamp value.

    Parameters
    ----------
    path : str | Path
        The path containing ${timestamp} variables to resolve.
    timestamp_value : str
        The timestamp value used to resolve the path.

    Returns
    -------
    Path
        The path with ${timestamp} variables resolved to the provided timestamp value.
    """
    template = Template(str(path))
    resolved_path = template.substitute(timestamp=timestamp_value)
    return Path(resolved_path)


def _resolve_timestamp_path_with_dir(
    path: str | Path, pattern: re.Pattern[str]
) -> Path:
    """Resolve the timestamp in the path with the latest available timestamp directory value.

    Parameters
    ----------
    path : str | Path
        The path containing ${timestamp} variables to resolve.
    pattern : re.Pattern[str]
        The pattern to use to match the timestamp directories.

    Returns
    -------
    Path
        The path with ${timestamp} variables resolved to the latest available timestamp directory value.

    Raises
    ------
    ValueError
        If the parent directory expecting to contain timestamp directories does not exist or is not a directory.
        Or if no timestamp directories are found in the parent directory that match the pattern.
    """
    path = Path(path)
    path_parts = path.parts
    parent_dir = Path(path_parts[0])
    found_timestamp_pattern = False
    for _, part in enumerate(path_parts[1:]):
        if part.lower() == "${timestamp}":
            found_timestamp_pattern = True
            break
        parent_dir = parent_dir / part

    # Path not using timestamp layout.
    if not found_timestamp_pattern:
        return path

    if not parent_dir.exists() or not parent_dir.is_dir():
        msg = f"Parent directory {parent_dir} does not exist or is not a directory."
        raise ValueError(msg)

    timestamp_dirs = [
        d for d in parent_dir.iterdir() if d.is_dir() and pattern.match(d.name)
    ]
    timestamp_dirs.sort(key=lambda d: d.name, reverse=True)
    if len(timestamp_dirs) == 0:
        msg = f"No timestamp directories found in {parent_dir} that match {pattern.pattern}."
        raise ValueError(msg)
    return _resolve_timestamp_path_with_value(path, timestamp_dirs[0].name)


def resolve_timestamp_path(
    path: str | Path,
    pattern_or_timestamp_value: re.Pattern[str] | str = re.compile(r"^\d{8}-\d{6}$"),
) -> Path:
    r"""Timestamp path resolver.

    Resolve the timestamp in the path with the given timestamp value or
    with the latest available timestamp directory matching the given pattern.

    Parameters
    ----------
    path : str | Path
        The path containing ${timestamp} variables to resolve.
    pattern_or_timestamp_value : re.Pattern[str] | str, default=re.compile(r"^\d{8}-\d{6}$")
        The pattern to use to match the timestamp directories or the timestamp value to use.
        If a string is provided, the path will be resolved with the given string value.
        Otherwise, the path will be resolved with the latest available timestamp directory
        that matches the given pattern.

    Returns
    -------
    Path
        The path with ${timestamp} variables resolved to the provided timestamp value or
        the latest available timestamp directory.

    Raises
    ------
    ValueError
        If the parent directory expecting to contain timestamp directories does not exist or is not a directory.
        Or if no timestamp directories are found in the parent directory that match the pattern.
    """
    if isinstance(pattern_or_timestamp_value, str):
        return _resolve_timestamp_path_with_value(path, pattern_or_timestamp_value)
    return _resolve_timestamp_path_with_dir(path, pattern_or_timestamp_value)
