# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Tests for the GraphRAG LLM module."""

# Register MOCK providers
from graphrag.config.enums import LLMType
from graphrag.llm.factory import LLMFactory
from tests.mock_provider import MockChatLLM, MockEmbeddingLLM


LLMFactory.register_chat(LLMType.MockChat, lambda **kwargs: MockChatLLM(**kwargs))
LLMFactory.register_embedding(LLMType.MockEmbedding, lambda **kwargs: MockEmbeddingLLM(**kwargs))
