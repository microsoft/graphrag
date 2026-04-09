# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag_input import InputConfig, InputType, create_input_reader
from graphrag_storage import StorageConfig, create_storage


async def test_parquet_loader_one_file():
    config = InputConfig(
        type=InputType.Parquet,
        file_pattern=".*\\.parquet$",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-parquet",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 2
    assert documents[0].title == "input.parquet (0)"
    assert documents[0].raw_data == {
        "title": "Hello",
        "text": "Hi how are you today?",
    }
    assert documents[1].title == "input.parquet (1)"


async def test_parquet_loader_one_file_with_title():
    config = InputConfig(
        type=InputType.Parquet,
        title_column="title",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-parquet",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 2
    assert documents[0].title == "Hello"
    assert documents[1].title == "World"


async def test_parquet_loader_text_content():
    config = InputConfig(
        type=InputType.Parquet,
        text_column="text",
        title_column="title",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-parquet",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 2
    assert documents[0].text == "Hi how are you today?"
    assert documents[1].text == "This is a test."
