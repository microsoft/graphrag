# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""CosmosDB Storage Tests."""

import json
import re
import sys
from datetime import datetime

import pytest

from graphrag.storage.cosmosdb_pipeline_storage import CosmosDBPipelineStorage

# cspell:disable-next-line well-known-key
WELL_KNOWN_COSMOS_CONNECTION_STRING = "AccountEndpoint=https://127.0.0.1:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="

# the cosmosdb emulator is only available on windows runners at this time
if not sys.platform.startswith("win"):
    pytest.skip(
        "encountered windows-only tests -- will skip for now", allow_module_level=True
    )


async def test_find():
    storage = CosmosDBPipelineStorage(
        connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
        database_name="testfind",
        container_name="testfindcontainer",
    )
    try:
        try:
            items = list(storage.find(file_pattern=re.compile(r".*\.json$")))
            items = [item[0] for item in items]
            assert items == []

            json_content = {
                "content": "Merry Christmas!",
            }
            await storage.set(
                "christmas.json", json.dumps(json_content), encoding="utf-8"
            )
            items = list(storage.find(file_pattern=re.compile(r".*\.json$")))
            items = [item[0] for item in items]
            assert items == ["christmas.json"]

            json_content = {
                "content": "Hello, World!",
            }
            await storage.set("test.json", json.dumps(json_content), encoding="utf-8")
            items = list(storage.find(file_pattern=re.compile(r".*\.json$")))
            items = [item[0] for item in items]
            assert items == ["christmas.json", "test.json"]

            output = await storage.get("test.json")
            output_json = json.loads(output)
            assert output_json["content"] == "Hello, World!"

            json_exists = await storage.has("christmas.json")
            assert json_exists is True
            json_exists = await storage.has("easter.json")
            assert json_exists is False
        finally:
            await storage.delete("test.json")
            output = await storage.get("test.json")
            assert output is None
    finally:
        await storage.clear()


async def test_child():
    storage = CosmosDBPipelineStorage(
        connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
        database_name="testchild",
        container_name="testchildcontainer",
    )
    try:
        child_storage = storage.child("child")
        assert type(child_storage) is CosmosDBPipelineStorage
    finally:
        await storage.clear()


async def test_clear():
    storage = CosmosDBPipelineStorage(
        connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
        database_name="testclear",
        container_name="testclearcontainer",
    )
    try:
        json_exists = {
            "content": "Merry Christmas!",
        }
        await storage.set("christmas.json", json.dumps(json_exists), encoding="utf-8")
        json_exists = {
            "content": "Happy Easter!",
        }
        await storage.set("easter.json", json.dumps(json_exists), encoding="utf-8")
        await storage.clear()

        items = list(storage.find(file_pattern=re.compile(r".*\.json$")))
        items = [item[0] for item in items]
        assert items == []

        output = await storage.get("easter.json")
        assert output is None

        assert storage._container_client is None  # noqa: SLF001
        assert storage._database_client is None  # noqa: SLF001
    finally:
        await storage.clear()


async def test_get_creation_date():
    storage = CosmosDBPipelineStorage(
        connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
        database_name="testclear",
        container_name="testclearcontainer",
    )
    try:
        json_content = {
            "content": "Happy Easter!",
        }
        await storage.set("easter.json", json.dumps(json_content), encoding="utf-8")

        creation_date = await storage.get_creation_date("easter.json")

        datetime_format = "%Y-%m-%d %H:%M:%S %z"
        parsed_datetime = datetime.strptime(creation_date, datetime_format).astimezone()

        assert parsed_datetime.strftime(datetime_format) == creation_date

    finally:
        await storage.clear()
