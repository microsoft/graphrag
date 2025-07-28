# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Blob Storage Tests."""

import os
import re
from datetime import datetime, timezone

import pandas as pd
from freezegun import freeze_time

from graphrag.storage.memory_pipeline_storage import (
    MemoryPipelineStorage,
    create_memory_storage,
)

__dirname__ = os.path.dirname(__file__)


async def test_find():
    input_files = {
        "input_files": {
            "tests/fixtures/text/input/dulce.txt": pd.DataFrame({
                "text": ["Dulce et decorum est"],
                "creation_date": [datetime(2023, 1, 1, tzinfo=timezone.utc)],
            }),
        }
    }

    storage = create_memory_storage(**input_files)

    items = list(
        storage.find(
            base_dir="any/path",
            file_pattern=re.compile(r".*\.txt$"),
            file_filter=None,
        )
    )
    assert items == [("tests/fixtures/text/input/dulce.txt", {})]
    output = await storage.get("tests/fixtures/text/input/dulce.txt")
    assert len(output) > 0

    await storage.set("test.txt", "Hello, World!", encoding="utf-8")
    output = await storage.get("test.txt")
    assert output == "Hello, World!"
    await storage.delete("test.txt")
    output = await storage.get("test.txt")
    assert output is None


@freeze_time("2023-10-01T15:55:00.12345")
async def test_get_creation_date():
    storage = MemoryPipelineStorage()

    creation_date = await storage.get_creation_date(
        "tests/fixtures/text/input/dulce.txt"
    )

    parsed_datetime = datetime.now(timezone.utc).isoformat()

    assert parsed_datetime == creation_date


def test_child():
    input_files = {
        "input_files": {
            "tests/fixtures/text/input/dulce.txt": pd.DataFrame({
                "text": ["Dulce et decorum est"],
                "creation_date": [datetime(2023, 1, 1, tzinfo=timezone.utc)],
            }),
        }
    }

    storage = create_memory_storage(**input_files)

    child_storage = storage.child("tests/fixtures/text/input")
    items = list(
        storage.find(base_dir="any/path", file_pattern=re.compile(r".*\.txt$"))
    )
    assert items == [("tests/fixtures/text/input/dulce.txt", {})]
    assert child_storage == storage

    items = list(
        child_storage.find(base_dir="any/path", file_pattern=re.compile(r".*\.txt$"))
    )
    assert items == [("tests/fixtures/text/input/dulce.txt", {})]
