# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Tests for the GraphRAG LLM module."""

# Register MOCK providers
from graphrag.config.enums import ModelType
from graphrag.language_model.factory import ChatModelFactory, EmbeddingModelFactory
from tests.mock_provider import MockChatLLM, MockEmbeddingLLM

ChatModelFactory().register(ModelType.MockChat, lambda **kwargs: MockChatLLM(**kwargs))
EmbeddingModelFactory().register(
    ModelType.MockEmbedding, lambda **kwargs: MockEmbeddingLLM(**kwargs)
)
