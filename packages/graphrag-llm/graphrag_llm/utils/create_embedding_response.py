# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Create embedding response utilities."""

from graphrag_llm.types import LLMEmbedding, LLMEmbeddingResponse, LLMEmbeddingUsage


def create_embedding_response(
    embeddings: list[float], batch_size: int = 1
) -> LLMEmbeddingResponse:
    """Create a CreateEmbeddingResponse object.

    Args:
        embeddings: List of embedding vectors.
        model: The model used to create the embeddings.

    Returns
    -------
        An LLMEmbeddingResponse object.
    """
    embeddings_objects = [
        LLMEmbedding(
            object="embedding",
            embedding=embeddings,
            index=index,
        )
        for index in range(batch_size)
    ]

    return LLMEmbeddingResponse(
        object="list",
        data=embeddings_objects,
        model="mock-model",
        usage=LLMEmbeddingUsage(
            prompt_tokens=0,
            total_tokens=0,
        ),
    )
