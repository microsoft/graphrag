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


async def test_csv_loader_preserves_multiline_fields(tmp_path):
    """Multiline quoted CSV fields must retain their internal newlines."""
    csv_content = (
        "title,text\r\n"
        '"Post 1","Line one.\nLine two.\nLine three."\r\n'
        '"Post 2","Single line."\r\n'
    )
    (tmp_path / "input.csv").write_text(csv_content, encoding="utf-8")
    config = InputConfig(
        type=InputType.Csv,
        text_column="text",
        title_column="title",
    )
    storage = create_storage(StorageConfig(base_dir=str(tmp_path)))
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 2
    assert documents[0].title == "Post 1"
    assert documents[0].text == "Line one.\nLine two.\nLine three."
    assert documents[1].title == "Post 2"
    assert documents[1].text == "Single line."
