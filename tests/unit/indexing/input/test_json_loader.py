# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.input.input_config import InputConfig
from graphrag.index.input.input_file_type import InputFileType
from graphrag.index.input.input_reader_factory import create_input_reader
from graphrag_storage import StorageConfig, create_storage


async def test_json_loader_one_file_one_object():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-json-one-object",
        ),
        file_type=InputFileType.Json,
        file_pattern=".*\\.json$",
    )
    storage = create_storage(config.storage)
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 1
    assert documents[0].title == "input.json"
    assert documents[0].raw_data == {
        "title": "Hello",
        "text": "Hi how are you today?",
    }


async def test_json_loader_one_file_multiple_objects():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-json-multiple-objects",
        ),
        file_type=InputFileType.Json,
    )
    storage = create_storage(config.storage)
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 3
    assert documents[0].title == "input.json (0)"
    assert documents[1].title == "input.json (1)"


async def test_json_loader_one_file_with_title():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-json-one-object",
        ),
        file_type=InputFileType.Json,
        title_column="title",
    )
    storage = create_storage(config.storage)
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 1
    assert documents[0].title == "Hello"


async def test_json_loader_multiple_files():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/multiple-jsons",
        ),
        file_type=InputFileType.Json,
    )
    storage = create_storage(config.storage)
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 4
