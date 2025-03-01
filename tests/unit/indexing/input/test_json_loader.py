# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.enums import InputFileType, InputType
from graphrag.config.models.input_config import InputConfig
from graphrag.index.input.factory import create_input


async def test_json_loader_one_file_one_object():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.json,
        file_pattern=".*\\.json$",
        base_dir="tests/unit/indexing/input/data/one-json-one-object",
    )
    documents = await create_input(config=config)
    assert documents.shape == (1, 4)
    assert documents["title"].iloc[0] == "input.json"


async def test_json_loader_one_file_multiple_objects():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.json,
        file_pattern=".*\\.json$",
        base_dir="tests/unit/indexing/input/data/one-json-multiple-objects",
    )
    documents = await create_input(config=config)
    print(documents)
    assert documents.shape == (3, 4)
    assert documents["title"].iloc[0] == "input.json"


async def test_json_loader_one_file_with_title():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.json,
        file_pattern=".*\\.json$",
        base_dir="tests/unit/indexing/input/data/one-json-one-object",
        title_column="title",
    )
    documents = await create_input(config=config)
    assert documents.shape == (1, 4)
    assert documents["title"].iloc[0] == "Hello"


async def test_json_loader_one_file_with_metadata():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.json,
        file_pattern=".*\\.json$",
        base_dir="tests/unit/indexing/input/data/one-json-one-object",
        title_column="title",
        metadata=["title"],
    )
    documents = await create_input(config=config)
    assert documents.shape == (1, 5)
    assert documents["metadata"][0] == {"title": "Hello"}


async def test_json_loader_multiple_files():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.json,
        file_pattern=".*\\.json$",
        base_dir="tests/unit/indexing/input/data/multiple-jsons",
    )
    documents = await create_input(config=config)
    assert documents.shape == (4, 4)
