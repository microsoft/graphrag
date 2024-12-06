# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""CosmosDB Storage Tests."""

import sys

import pytest

# the cosmosdb emulator is only available on windows runners at this time
if not sys.platform.startswith("win"):
    pytest.skip("skipping windows-only tests", allow_module_level=True)


def test_find():
    print("test_find")
    assert True


def test_child():
    print("test_child")
    assert True
