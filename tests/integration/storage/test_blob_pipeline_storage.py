# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Blob Storage Tests."""

import re
from datetime import datetime

from graphrag.storage.blob_pipeline_storage import BlobPipelineStorage

# cspell:disable-next-line well-known-key
WELL_KNOWN_BLOB_STORAGE_KEY = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"


async def test_find():
    storage = BlobPipelineStorage(
        connection_string=WELL_KNOWN_BLOB_STORAGE_KEY,
        container_name="testfind",
    )
    try:
        try:
            items = list(
                storage.find(base_dir="input", file_pattern=re.compile(r".*\.txt$"))
            )
            items = [item[0] for item in items]
            assert items == []

            await storage.set(
                "input/christmas.txt", "Merry Christmas!", encoding="utf-8"
            )
            items = list(
                storage.find(base_dir="input", file_pattern=re.compile(r".*\.txt$"))
            )
            items = [item[0] for item in items]
            assert items == ["input/christmas.txt"]

            await storage.set("test.txt", "Hello, World!", encoding="utf-8")
            items = list(storage.find(file_pattern=re.compile(r".*\.txt$")))
            items = [item[0] for item in items]
            assert items == ["input/christmas.txt", "test.txt"]

            output = await storage.get("test.txt")
            assert output == "Hello, World!"
        finally:
            await storage.delete("test.txt")
            output = await storage.get("test.txt")
            assert output is None
    finally:
        storage._delete_container()  # noqa: SLF001


async def test_dotprefix():
    storage = BlobPipelineStorage(
        connection_string=WELL_KNOWN_BLOB_STORAGE_KEY,
        container_name="testfind",
        path_prefix=".",
    )
    try:
        await storage.set("input/christmas.txt", "Merry Christmas!", encoding="utf-8")
        items = list(storage.find(file_pattern=re.compile(r".*\.txt$")))
        items = [item[0] for item in items]
        assert items == ["input/christmas.txt"]
    finally:
        storage._delete_container()  # noqa: SLF001


async def test_get_creation_date():
    storage = BlobPipelineStorage(
        connection_string=WELL_KNOWN_BLOB_STORAGE_KEY,
        container_name="testfind",
        path_prefix=".",
    )
    try:
        await storage.set("input/christmas.txt", "Merry Christmas!", encoding="utf-8")
        creation_date = await storage.get_creation_date("input/christmas.txt")

        datetime_format = "%Y-%m-%d %H:%M:%S %z"
        parsed_datetime = datetime.strptime(creation_date, datetime_format).astimezone()

        assert parsed_datetime.strftime(datetime_format) == creation_date
    finally:
        storage._delete_container()  # noqa: SLF001


async def test_child():
    parent = BlobPipelineStorage(
        connection_string=WELL_KNOWN_BLOB_STORAGE_KEY,
        container_name="testchild",
    )
    try:
        try:
            storage = parent.child("input")
            await storage.set("christmas.txt", "Merry Christmas!", encoding="utf-8")
            items = list(storage.find(re.compile(r".*\.txt$")))
            items = [item[0] for item in items]
            assert items == ["christmas.txt"]

            await storage.set("test.txt", "Hello, World!", encoding="utf-8")
            items = list(storage.find(re.compile(r".*\.txt$")))
            items = [item[0] for item in items]
            print("FOUND", items)
            assert items == ["christmas.txt", "test.txt"]

            output = await storage.get("test.txt")
            assert output == "Hello, World!"

            items = list(parent.find(re.compile(r".*\.txt$")))
            items = [item[0] for item in items]
            print("FOUND ITEMS", items)
            assert items == ["input/christmas.txt", "input/test.txt"]
        finally:
            await parent.delete("input/test.txt")
            has_test = await parent.has("input/test.txt")
            assert not has_test
    finally:
        parent._delete_container()  # noqa: SLF001
