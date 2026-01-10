# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag_input import InputConfig, InputType, create_input_reader
from graphrag_storage import StorageConfig, create_storage


async def test_text_loader_one_file():
    config = InputConfig(
        type=InputType.Text,
        file_pattern=".*\\.txt$",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-txt",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 1
    assert documents[0].title == "input.txt"
    assert documents[0].raw_data is None


async def test_text_loader_multiple_files():
    config = InputConfig(
        type=InputType.Text,
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/multiple-txts",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 2
