# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations
from typing import Protocol, List, Any

class EmbeddingLLM(Protocol):
    def embed(self, text: str, **kwargs: Any) -> List[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: The text to generate an embedding for.
            **kwargs: Additional keyword arguments (e.g., model parameters).

        Returns:
            A list of floats representing the embedding vector.
        """
        ...