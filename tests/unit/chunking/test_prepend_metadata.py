# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.chunking.prepend_metadata import prepend_metadata


def test_prepend_metadata_one_row():
    """Test prepending metadata to chunks"""
    chunks = ["This is a test.", "Another sentence."]
    metadata = {"message": "hello"}
    results = [prepend_metadata(chunk, metadata) for chunk in chunks]
    assert results[0] == "message: hello\nThis is a test."
    assert results[1] == "message: hello\nAnother sentence."


def test_prepend_metadata_multiple_rows():
    """Test prepending metadata to chunks"""
    chunks = ["This is a test.", "Another sentence."]
    metadata = {"message": "hello", "tag": "first"}
    results = [prepend_metadata(chunk, metadata) for chunk in chunks]
    assert results[0] == "message: hello\ntag: first\nThis is a test."
    assert results[1] == "message: hello\ntag: first\nAnother sentence."


def test_prepend_metadata_custom_delimiters():
    """Test prepending metadata to chunks"""
    chunks = ["This is a test.", "Another sentence."]
    metadata = {"message": "hello", "tag": "first"}
    results = [
        prepend_metadata(chunk, metadata, delimiter="-", line_delimiter="_")
        for chunk in chunks
    ]
    assert results[0] == "message-hello_tag-first_This is a test."
    assert results[1] == "message-hello_tag-first_Another sentence."
