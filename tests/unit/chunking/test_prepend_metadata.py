# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag_chunking.transformers import add_metadata


def test_add_metadata_one_row():
    """Test prepending metadata to chunks"""
    chunks = ["This is a test.", "Another sentence."]
    metadata = {"message": "hello"}
    transformer = add_metadata(metadata)
    results = [transformer(chunk) for chunk in chunks]
    assert results[0] == "message: hello\nThis is a test."
    assert results[1] == "message: hello\nAnother sentence."


def test_add_metadata_one_row_append():
    """Test prepending metadata to chunks"""
    chunks = ["This is a test.", "Another sentence."]
    metadata = {"message": "hello"}
    transformer = add_metadata(metadata, append=True)
    results = [transformer(chunk) for chunk in chunks]
    assert results[0] == "This is a test.message: hello\n"
    assert results[1] == "Another sentence.message: hello\n"


def test_add_metadata_multiple_rows():
    """Test prepending metadata to chunks"""
    chunks = ["This is a test.", "Another sentence."]
    metadata = {"message": "hello", "tag": "first"}
    transformer = add_metadata(metadata)
    results = [transformer(chunk) for chunk in chunks]
    assert results[0] == "message: hello\ntag: first\nThis is a test."
    assert results[1] == "message: hello\ntag: first\nAnother sentence."


def test_add_metadata_custom_delimiters():
    """Test prepending metadata to chunks"""
    chunks = ["This is a test.", "Another sentence."]
    metadata = {"message": "hello", "tag": "first"}
    transformer = add_metadata(metadata, delimiter="-", line_delimiter="_")
    results = [transformer(chunk) for chunk in chunks]
    assert results[0] == "message-hello_tag-first_This is a test."
    assert results[1] == "message-hello_tag-first_Another sentence."
