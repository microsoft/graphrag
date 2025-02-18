# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

from typing import Any, Protocol


class EmbeddingLLM(Protocol):
    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: The text to generate an embedding for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns:
            A list of floats representing the embedding vector.
        """
        ...


class ChatLLM(Protocol):
    def chat(self, text: str, **kwargs: Any) -> str:
        """
        Generate a response for the given text.

        Args:
            text: The text to generate a response for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns:
            A string representing the response.
        """
        ...
