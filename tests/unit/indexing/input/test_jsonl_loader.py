# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag_input import InputConfig, InputType, create_input_reader
from graphrag_storage import StorageConfig, create_storage


async def test_jsonl_loader_one_file_multiple_objects():
    config = InputConfig(
        type=InputType.JsonLines,
        file_pattern=".*\\.jsonl$",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-jsonl",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 3
    assert documents[0].title == "input.jsonl (0)"
    assert documents[0].raw_data == {
        "title": "Hello",
        "text": "Hi how are you today?",
    }
    assert documents[1].title == "input.jsonl (1)"


async def test_jsonl_loader_one_file_with_title():
    config = InputConfig(
        type=InputType.JsonLines,
        title_column="title",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-jsonl",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 3
    assert documents[0].title == "Hello"


async def test_jsonl_loader_ignores_blank_lines(tmp_path):
    (tmp_path / "input.jsonl").write_text(
        '{"title":"Hello","text":"Hi"}\n\n   \n{"title":"Goodbye","text":"Bye"}\n',
        encoding="utf-8",
    )
    config = InputConfig(
        type=InputType.JsonLines,
        title_column="title",
    )
    storage = create_storage(
        StorageConfig(
            base_dir=str(tmp_path),
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 2
    assert [doc.title for doc in documents] == ["Hello", "Goodbye"]
    assert [doc.text for doc in documents] == ["Hi", "Bye"]
