# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.enums import InputFileType, InputType
from graphrag.config.models.input_config import InputConfig
from graphrag.index.input.factory import create_input


async def test_txt_loader_one_file():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.text,
        file_pattern=".*\\.txt$",
        base_dir="tests/unit/indexing/input/data/one-txt",
    )
    documents = await create_input(config=config)
    assert documents.shape == (1, 4)
    assert documents["title"].iloc[0] == "input.txt"


async def test_txt_loader_one_file_with_metadata():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.text,
        file_pattern=".*\\.txt$",
        base_dir="tests/unit/indexing/input/data/one-txt",
        metadata=["title"],
    )
    documents = await create_input(config=config)
    assert documents.shape == (1, 5)
    # unlike csv, we cannot set the title to anything other than the filename
    assert documents["metadata"][0] == {"title": "input.txt"}


async def test_txt_loader_multiple_files():
    config = InputConfig(
        type=InputType.file,
        file_type=InputFileType.text,
        file_pattern=".*\\.txt$",
        base_dir="tests/unit/indexing/input/data/multiple-txts",
    )
    documents = await create_input(config=config)
    assert documents.shape == (2, 4)
