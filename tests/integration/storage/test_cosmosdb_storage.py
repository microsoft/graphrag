# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""CosmosDB Storage Tests."""

import re
import sys

import pytest

from graphrag.storage.cosmosdb_pipeline_storage import CosmosDBPipelineStorage

# cspell:disable-next-line well-known-key
WELL_KNOWN_COSMOS_CONNECTION_STRING = "AccountEndpoint=https://localhost:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==;"

# the cosmosdb emulator is only available on windows runners at this time
if not sys.platform.startswith("win"):
    pytest.skip(
        "encountered windows-only tests -- will skip for now", allow_module_level=True
    )


async def test_find():
    storage = CosmosDBPipelineStorage(
        connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
        database_name="testfind",
    )
    try:
        try:
            items = list(
                storage.find(base_dir="input", file_pattern=re.compile(r".*\.txt$"))
            )
            items = [item[0] for item in items]
            assert items == []

            await storage.set("christmas.txt", "Merry Christmas!", encoding="utf-8")
            items = list(
                storage.find(base_dir="input", file_pattern=re.compile(r".*\.txt$"))
            )
            items = [item[0] for item in items]
            assert items == ["christmas.txt"]

            await storage.set("test.txt", "Hello, World!", encoding="utf-8")
            items = list(storage.find(file_pattern=re.compile(r".*\.txt$")))
            items = [item[0] for item in items]
            assert items == ["christmas.txt", "test.txt"]

            output = await storage.get("test.txt")
            assert output == "Hello, World!"
        finally:
            await storage.delete("test.txt")
            output = await storage.get("test.txt")
            assert output is None
    finally:
        storage._delete_container()  # noqa: SLF001


def test_child():
    assert True
