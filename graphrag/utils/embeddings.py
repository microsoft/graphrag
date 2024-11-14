# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utilities for working with embeddings stores."""

from graphrag.index.config.embeddings import all_embeddings


def create_collection_name(
    container_name: str, embedding_name: str, validate: bool = True
) -> str:
    """
    Create a collection name for the embedding store.

    Within any given vector store, we can have multiple sets of embeddings organized into projects.
    The `container` param is used for this partitioning, and is added as a prefix to the collection name for differentiation.

    The embedding name is fixed, with the available list defined in graphrag.index.config.embeddings

    Note that we use dot notation in our names, but many vector stores do not support this - so we convert to dashes.
    """
    if validate and embedding_name not in all_embeddings:
        msg = f"Invalid embedding name: {embedding_name}"
        raise KeyError(msg)
    return f"{container_name}-{embedding_name}".replace(".", "-")
