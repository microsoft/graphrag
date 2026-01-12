# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag_input import InputConfig, InputType, create_input_reader
from graphrag_storage import StorageConfig, create_storage


async def test_csv_loader_one_file():
    config = InputConfig(
        type=InputType.Csv,
        file_pattern=".*\\.csv$",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-csv",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 2
    assert documents[0].title == "input.csv (0)"
    assert documents[0].raw_data == {
        "title": "Hello",
        "text": "Hi how are you today?",
    }
    assert documents[1].title == "input.csv (1)"


async def test_csv_loader_one_file_with_title():
    config = InputConfig(
        type=InputType.Csv,
        title_column="title",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-csv",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 2
    assert documents[0].title == "Hello"


async def test_csv_loader_multiple_files():
    config = InputConfig(
        type=InputType.Csv,
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/multiple-csvs",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 4
