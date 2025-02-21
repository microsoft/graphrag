# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Tests for the GraphRAG LLM module."""

# Register MOCK providers
from graphrag.config.enums import ModelType
from graphrag.language_model.factory import ModelFactory
from tests.mock_provider import MockChatLLM, MockEmbeddingLLM

ModelFactory.register_chat(ModelType.MockChat, lambda **kwargs: MockChatLLM(**kwargs))
ModelFactory.register_embedding(
    ModelType.MockEmbedding, lambda **kwargs: MockEmbeddingLLM(**kwargs)
)
