# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing fnllm model provider definitions."""


class MockChatLLM:
    """A mock chat LLM provider."""

    def chat(self, text: str, **kwargs) -> str:
        """Generate a response to the input text."""
        return "Mock response"


class MockEmbeddingLLM:
    """A mock embedding LLM provider."""

    def embed(self, text: str, **kwargs: Any) -> list:
        """Generate an embedding for the input text."""
        return [0.0, 0.0, 0.0]
