# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Base llm protocol definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from graphrag.llm.response.base import LLMResponse


class EmbeddingLLM(Protocol):
    """
    Protocol for an embedding-based Language Model (LLM).

    This protocol defines the methods required for an embedding-based LLM.
    """

    async def embed(self, text: str | list[str], **kwargs: Any) -> list[list[float]]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: The text to generate an embedding for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            A list of floats representing the embedding vector.
        """
        ...


class ChatLLM(Protocol):
    """
    Protocol for a chat-based Language Model (LLM).

    This protocol defines the methods required for a chat-based LLM.
    Prompt is always required for the chat method, and any other keyword arguments are forwarded to the LLM provider.
    """

    async def chat(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Generate a response for the given text.

        Args:
            prompt: The text to generate a response for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            A string representing the response.

        """
        ...
