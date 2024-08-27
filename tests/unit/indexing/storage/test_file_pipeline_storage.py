# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Blob Storage Tests."""

import os
import re
from pathlib import Path

from graphrag.common.storage.file_pipeline_storage import FilePipelineStorage

__dirname__ = os.path.dirname(__file__)


async def test_find():
    storage = FilePipelineStorage()
    items = list(
        storage.find(
            base_dir="tests/fixtures/text",
            file_pattern=re.compile(r".*\.txt$"),
            progress=None,
            file_filter=None,
        )
    )
    assert items == [(str(Path("tests/fixtures/text/input/dulce.txt")), {})]
    output = await storage.get("tests/fixtures/text/input/dulce.txt")
    assert len(output) > 0

    await storage.set("test.txt", "Hello, World!", encoding="utf-8")
    output = await storage.get("test.txt")
    assert output == "Hello, World!"
    await storage.delete("test.txt")
    output = await storage.get("test.txt")
    assert output is None


async def test_child():
    storage = FilePipelineStorage()
    storage = storage.child("tests/fixtures/text")
    items = list(storage.find(re.compile(r".*\.txt$")))
    assert items == [(str(Path("input/dulce.txt")), {})]

    output = await storage.get("input/dulce.txt")
    assert len(output) > 0

    await storage.set("test.txt", "Hello, World!", encoding="utf-8")
    output = await storage.get("test.txt")
    assert output == "Hello, World!"
    await storage.delete("test.txt")
    output = await storage.get("test.txt")
    assert output is None
