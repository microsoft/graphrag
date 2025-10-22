# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Base llm protocol definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from graphrag.config.models.language_model_config import LanguageModelConfig
    from graphrag.language_model.response.base import ModelResponse


class EmbeddingModel(Protocol):
    """
    Protocol for an embedding-based Language Model (LM).

    This protocol defines the methods required for an embedding-based LM.
    """

    config: LanguageModelConfig
    """Passthrough of the config used to create the model instance."""

    async def aembed_batch(
        self, text_list: list[str], **kwargs: Any
    ) -> list[list[float]]:
        """
        Generate an embedding vector for the given list of strings.

        Args:
            text: The text to generate an embedding for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            A collections of list of floats representing the embedding vector for each item in the batch.
        """
        ...

    async def aembed(self, text: str, **kwargs: Any) -> list[float]:
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

    def embed_batch(self, text_list: list[str], **kwargs: Any) -> list[list[float]]:
        """
        Generate an embedding vector for the given list of strings.

        Args:
            text: The text to generate an embedding for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            A collections of list of floats representing the embedding vector for each item in the batch.
        """
        ...

    def embed(self, text: str, **kwargs: Any) -> list[float]:
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


class ChatModel(Protocol):
    """
    Protocol for a chat-based Language Model (LM).

    This protocol defines the methods required for a chat-based LM.
    Prompt is always required for the chat method, and any other keyword arguments are forwarded to the Model provider.
    """

    config: LanguageModelConfig
    """Passthrough of the config used to create the model instance."""

    async def achat(
        self, prompt: str, history: list | None = None, **kwargs: Any
    ) -> ModelResponse:
        """
        Generate a response for the given text.

        Args:
            prompt: The text to generate a response for.
            history: The conversation history.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            A string representing the response.

        """
        ...

    async def achat_stream(
        self, prompt: str, history: list | None = None, **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        Generate a response for the given text using a streaming interface.

        Args:
            prompt: The text to generate a response for.
            history: The conversation history.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            A generator that yields strings representing the response.
        """
        yield ""  # Yield an empty string so that the function is recognized as a generator
        ...

    def chat(
        self, prompt: str, history: list | None = None, **kwargs: Any
    ) -> ModelResponse:
        """
        Generate a response for the given text.

        Args:
            prompt: The text to generate a response for.
            history: The conversation history.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            A string representing the response.

        """
        ...

    def chat_stream(
        self, prompt: str, history: list | None = None, **kwargs: Any
    ) -> Generator[str, None]:
        """
        Generate a response for the given text using a streaming interface.

        Args:
            prompt: The text to generate a response for.
            history: The conversation history.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns
        -------
            A generator that yields strings representing the response.
        """
        ...
