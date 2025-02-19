# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""CosmosDB Storage Tests."""

import json
import re
import sys
from datetime import datetime

import pytest

from graphrag.storage.documentdb_pipeline_storage import DocumentDBPipelineStorage


async def test_find():
    storage = DocumentDBPipelineStorage(
        database_name = "documentdb",
        collection = "testfindtable",
        user = "admin",
        password = "admin",
        host = "host.docker.internal",
        port = 9712,
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

            items = list(storage.find(file_pattern=re.compile(r".*\.json$"), file_filter={"key": "test.json"}))
            items = [item[0] for item in items]
            assert items == ["test.json"]

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
    storage = DocumentDBPipelineStorage(
        database_name = "documentdb",
        collection = "testfindtable",
        user = "admin",
        password = "admin",
        host = "host.docker.internal",
        port = 9712,
    )
    try:
        child_storage = storage.child("child")
        assert type(child_storage) is DocumentDBPipelineStorage
    finally:
        await storage.clear()


async def test_clear():
    storage = DocumentDBPipelineStorage(
        database_name = "documentdb",
        collection = "testfindtable",
        user = "admin",
        password = "admin",
        host = "host.docker.internal",
        port = 9712,
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
    finally:
        # await storage.clear()
        print("Table cleared")


async def test_get_creation_date():
    storage = DocumentDBPipelineStorage(
        database_name = "documentdb",
        collection = "testfindtable",
        user = "admin",
        password = "admin",
        host = "host.docker.internal",
        port = 9712,
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
