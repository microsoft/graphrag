# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import pytest

from graphrag.config.embeddings import create_index_name


def test_create_index_name():
    collection = create_index_name("default", "entity.title")
    assert collection == "default-entity-title"


def test_create_index_name_invalid_embedding_throws():
    with pytest.raises(KeyError):
        create_index_name("default", "invalid.name")


def test_create_index_name_invalid_embedding_does_not_throw():
    collection = create_index_name("default", "invalid.name", validate=False)
    assert collection == "default-invalid-name"
