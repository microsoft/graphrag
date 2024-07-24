# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os
import unittest

from graphrag.index.cache import (
    JsonPipelineCache,
)
from graphrag.index.storage.file_pipeline_storage import (
    FilePipelineStorage,
)

TEMP_DIR = "./.tmp"


def create_cache():
    storage = FilePipelineStorage(os.path.join(os.getcwd(), ".tmp"))
    return JsonPipelineCache(storage)


class TestFilePipelineCache(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.cache = create_cache()

    def tearDown(self):
        asyncio.run(self.cache.clear())

    async def test_cache_clear(self):
        # Create a cache directory
        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)
        with open(f"{TEMP_DIR}/test1", "w") as f:
            f.write("This is test1 file.")
        with open(f"{TEMP_DIR}/test2", "w") as f:
            f.write("This is test2 file.")

        # this invokes cache.clear()
        await self.cache.clear()

        # Check if the cache directory is empty
        files = os.listdir(TEMP_DIR)
        assert len(files) == 0

    async def test_child_cache(self):
        await self.cache.set("test1", "test1")
        assert os.path.exists(f"{TEMP_DIR}/test1")

        child = self.cache.child("test")
        assert os.path.exists(f"{TEMP_DIR}/test")

        await child.set("test2", "test2")
        assert os.path.exists(f"{TEMP_DIR}/test/test2")

        await self.cache.set("test1", "test1")
        await self.cache.delete("test1")
        assert not os.path.exists(f"{TEMP_DIR}/test1")

    async def test_cache_has(self):
        test1 = "this is a test file"
        await self.cache.set("test1", test1)

        assert await self.cache.has("test1")
        assert not await self.cache.has("NON_EXISTENT")
        assert await self.cache.get("NON_EXISTENT") is None

    async def test_get_set(self):
        test1 = "this is a test file"
        test2 = "\\n test"
        test3 = "\\\\\\"
        await self.cache.set("test1", test1)
        await self.cache.set("test2", test2)
        await self.cache.set("test3", test3)
        assert await self.cache.get("test1") == test1
        assert await self.cache.get("test2") == test2
        assert await self.cache.get("test3") == test3
