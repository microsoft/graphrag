# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag_input import InputConfig, InputType, create_input_reader
from graphrag_storage import StorageConfig, create_storage


async def test_json_loader_one_file_one_object():
    config = InputConfig(
        type=InputType.Json,
        file_pattern=".*\\.json$",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-json-one-object",
        )
    )
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
        type=InputType.Json,
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-json-multiple-objects",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 3
    assert documents[0].title == "input.json (0)"
    assert documents[1].title == "input.json (1)"


async def test_json_loader_one_file_with_title():
    config = InputConfig(
        type=InputType.Json,
        title_column="title",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-json-one-object",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 1
    assert documents[0].title == "Hello"


async def test_json_loader_multiple_files():
    config = InputConfig(
        type=InputType.Json,
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/multiple-jsons",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 4
