# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag_input import InputConfig, InputType, create_input_reader
from graphrag_storage import StorageConfig, create_storage


# these tests just confirm we can load files with MarkItDown,
# and use html specifically because it requires no additional dependency installation
async def test_markitdown_loader_one_file():
    config = InputConfig(
        type=InputType.MarkItDown,
        file_pattern=".*\\.html$",
    )
    storage = create_storage(
        StorageConfig(
            base_dir="tests/unit/indexing/input/data/one-html",
        )
    )
    reader = create_input_reader(config, storage)
    documents = await reader.read_files()
    assert len(documents) == 1
    # markitdown will extract the title and body from the HTML if present and clean them
    assert documents[0].title == "Test"
    assert documents[0].text == "Hi how are you today?"
    assert documents[0].raw_data is None
