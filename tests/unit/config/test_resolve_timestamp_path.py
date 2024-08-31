# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from pathlib import Path

from graphrag.config.resolve_timestamp_path import resolve_timestamp_path


def test_resolve_timestamp_path_no_timestamp_with_run_id():
    path = Path("path/to/data")
    result = resolve_timestamp_path(path, "20240812-121000")
    assert result == path


def test_resolve_timestamp_path_no_timestamp_without_run_id():
    path = Path("path/to/data")
    result = resolve_timestamp_path(path)
    assert result == path


def test_resolve_timestamp_path_with_timestamp_and_run_id():
    path = Path("some/path/${timestamp}/data")
    expected = Path("some/path/20240812/data")
    result = resolve_timestamp_path(path, "20240812")
    assert result == expected


def test_resolve_timestamp_path_with_timestamp_and_inferred_directory():
    cwd = Path(__file__).parent
    path = cwd / "fixtures/timestamp_dirs/${timestamp}/data"
    expected = cwd / "fixtures/timestamp_dirs/20240812-120000/data"
    result = resolve_timestamp_path(path)
    assert result == expected
