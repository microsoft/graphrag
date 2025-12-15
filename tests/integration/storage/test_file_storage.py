# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Blob Storage Tests."""

import os
import re
from datetime import datetime
from pathlib import Path

from graphrag_storage.file_storage import (
    FileStorage,
)

__dirname__ = os.path.dirname(__file__)


async def test_find():
    storage = FileStorage(base_dir="tests/fixtures/text/input")
    items = list(storage.find(file_pattern=re.compile(r".*\.txt$")))
    assert items == [str(Path("dulce.txt"))]
    output = await storage.get("dulce.txt")
    assert len(output) > 0

    await storage.set("test.txt", "Hello, World!", encoding="utf-8")
    output = await storage.get("test.txt")
    assert output == "Hello, World!"
    await storage.delete("test.txt")
    output = await storage.get("test.txt")
    assert output is None


async def test_get_creation_date():
    storage = FileStorage(
        base_dir="tests/fixtures/text/input",
    )

    creation_date = await storage.get_creation_date("dulce.txt")

    datetime_format = "%Y-%m-%d %H:%M:%S %z"
    parsed_datetime = datetime.strptime(creation_date, datetime_format).astimezone()

    assert parsed_datetime.strftime(datetime_format) == creation_date


async def test_child():
    storage = FileStorage(base_dir="")
    storage = storage.child("tests/fixtures/text/input")
    items = list(storage.find(re.compile(r".*\.txt$")))
    assert items == [str(Path("dulce.txt"))]

    output = await storage.get("dulce.txt")
    assert len(output) > 0

    await storage.set("test.txt", "Hello, World!", encoding="utf-8")
    output = await storage.get("test.txt")
    assert output == "Hello, World!"
    await storage.delete("test.txt")
    output = await storage.get("test.txt")
    assert output is None
