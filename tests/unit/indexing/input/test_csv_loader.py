# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.enums import InputFileType, InputType
from graphrag.config.models.input_config import InputConfig
from graphrag.index.input.factory import create_input


async def test_csv_loader_one_file():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.csv,
        file_pattern=".*\\.csv$",
        base_dir="tests/unit/indexing/input/data/one-csv",
    )
    documents = await create_input(config=config)
    assert documents.shape == (2, 4)
    assert documents["title"].iloc[0] == "input.csv"


async def test_csv_loader_one_file_with_title():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.csv,
        file_pattern=".*\\.csv$",
        base_dir="tests/unit/indexing/input/data/one-csv",
        title_column="title",
    )
    documents = await create_input(config=config)
    assert documents.shape == (2, 4)
    assert documents["title"].iloc[0] == "Hello"


async def test_csv_loader_one_file_with_metadata():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.csv,
        file_pattern=".*\\.csv$",
        base_dir="tests/unit/indexing/input/data/one-csv",
        title_column="title",
        metadata=["title"],
    )
    documents = await create_input(config=config)
    assert documents.shape == (2, 5)
    assert documents["metadata"][0] == {"title": "Hello"}


async def test_csv_loader_multiple_files():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.csv,
        file_pattern=".*\\.csv$",
        base_dir="tests/unit/indexing/input/data/multiple-csvs",
    )
    documents = await create_input(config=config)
    assert documents.shape == (4, 4)
