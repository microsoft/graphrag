# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from pathlib import Path

import pytest

from graphrag.query.cli import _infer_data_dir


def test_infer_data_dir():
    root = "./tests/unit/query/data/defaults"
    result = Path(_infer_data_dir(root))
    assert result.match("20240812-121000/artifacts") is True

def test_infer_data_dir_ignores_hidden_files():
    """ A hidden file, starting with '.', will naturally be selected as latest data directory."""
    root = "./tests/unit/query/data/hidden"
    result = Path(_infer_data_dir(root))
    print(result)
    assert result.match("20240812-121000/artifacts") is True

def test_infer_data_dir_ignores_non_numeric():
    root = "./tests/unit/query/data/non-numeric"
    result = Path(_infer_data_dir(root))
    assert result.match("20240812-121000/artifacts") is True

def test_infer_data_dir_throws_on_no_match():
    root = "./tests/unit/query/data/empty"
    with pytest.raises(ValueError):
        _infer_data_dir(root)