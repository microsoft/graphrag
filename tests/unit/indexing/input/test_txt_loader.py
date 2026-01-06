# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.input.input_config import InputConfig
from graphrag.index.input.input_file_type import InputFileType
from graphrag.index.input.input_reader_factory import create_input_reader
from graphrag_storage import StorageConfig, create_storage


async def test_txt_loader_one_file():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-txt",
        ),
        file_type=InputFileType.Text,
        file_pattern=".*\\.txt$",
    )
    storage = create_storage(config.storage)
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 1
    assert documents[0].title == "input.txt"
    assert documents[0].metadata is None


async def test_txt_loader_one_file_with_metadata():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-txt",
        ),
        file_type=InputFileType.Text,
        file_pattern=".*\\.txt$",
        metadata=["title"],
    )
    storage = create_storage(config.storage)
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 1
    # unlike csv, we cannot set the title to anything other than the filename
    assert documents[0].metadata == {"title": "input.txt"}


async def test_txt_loader_multiple_files():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/multiple-txts",
        ),
        file_type=InputFileType.Text,
        file_pattern=".*\\.txt$",
    )
    storage = create_storage(config.storage)
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 2
