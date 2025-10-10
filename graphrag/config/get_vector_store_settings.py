# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing get_vector_store_settings."""

from graphrag.config.models.graph_rag_config import GraphRagConfig


def get_vector_store_settings(
    settings: GraphRagConfig,
    vector_store_params: dict | None = None,
) -> dict:
    """Transform GraphRAG config into settings for workflows."""
    vector_store_settings = settings.vector_store.model_dump()

    #
    # If we get to this point, settings.vector_store is defined, and there's a specific setting for this embedding.
    # settings.vector_store.base contains connection information, or may be undefined
    # settings.vector_store.<vector_name> contains the specific settings for this embedding
    #
    return {
        **(vector_store_params or {}),
        **(vector_store_settings),
    }
