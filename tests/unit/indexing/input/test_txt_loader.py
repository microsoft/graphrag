# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.enums import InputFileType
from graphrag.config.models.input_config import InputConfig
from graphrag.config.models.storage_config import StorageConfig
from graphrag.index.input.factory import create_input
from graphrag.utils.api import create_storage_from_config


async def test_txt_loader_one_file():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-txt",
        ),
        file_type=InputFileType.text,
        file_pattern=".*\\.txt$",
    )
    storage = create_storage_from_config(config.storage)
    documents = await create_input(config=config, storage=storage)
    assert documents.shape == (1, 4)
    assert documents["title"].iloc[0] == "input.txt"


async def test_txt_loader_one_file_with_metadata():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-txt",
        ),
        file_type=InputFileType.text,
        file_pattern=".*\\.txt$",
        metadata=["title"],
    )
    storage = create_storage_from_config(config.storage)
    documents = await create_input(config=config, storage=storage)
    assert documents.shape == (1, 5)
    # unlike csv, we cannot set the title to anything other than the filename
    assert documents["metadata"][0] == {"title": "input.txt"}


async def test_txt_loader_multiple_files():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/multiple-txts",
        ),
        file_type=InputFileType.text,
        file_pattern=".*\\.txt$",
    )
    storage = create_storage_from_config(config.storage)
    documents = await create_input(config=config, storage=storage)
    assert documents.shape == (2, 4)
