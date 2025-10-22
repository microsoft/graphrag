# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Gather Embeddings."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphrag_llm.types import LLMEmbeddingResponse


def gather_embeddings(
    response: "LLMEmbeddingResponse",
) -> list[list[float]]:
    """Gather embeddings from an embedding response.

    Args
    ----
        response: LLMEmbeddingResponse
            The embedding response or a list of embeddings.

    Returns
    -------
        The gathered embeddings as a list of lists of floats.
    """
    return [data.embedding for data in response.data]
