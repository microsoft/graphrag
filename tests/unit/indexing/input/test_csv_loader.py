# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.input.input_config import InputConfig
from graphrag.index.input.input_file_type import InputFileType
from graphrag.index.input.input_reader_factory import (
    create_input_reader,
)
from graphrag_storage import StorageConfig, create_storage


async def test_csv_loader_one_file():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-csv",
        ),
        file_type=InputFileType.Csv,
        file_pattern=".*\\.csv$",
    )
    storage = create_storage(config.storage)
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
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-csv",
        ),
        file_type=InputFileType.Csv,
        title_column="title",
    )
    storage = create_storage(config.storage)
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 2
    assert documents[0].title == "Hello"


async def test_csv_loader_multiple_files():
    config = InputConfig(
        storage=StorageConfig(
            base_dir="tests/unit/indexing/input/data/multiple-csvs",
        ),
        file_type=InputFileType.Csv,
    )
    storage = create_storage(config.storage)
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 4
