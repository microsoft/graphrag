# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing get_embedding_settings."""

from graphrag.config.models.graph_rag_config import GraphRagConfig


def get_embedding_settings(
    settings: GraphRagConfig,
    vector_store_params: dict | None = None,
) -> dict:
    """Transform GraphRAG config into settings for workflows."""
    # TEMP
    embeddings_llm_settings = settings.get_language_model_config(
        settings.embed_text.model_id
    )
    vector_store_settings = settings.get_vector_store_config(
        settings.embed_text.vector_store_id
    ).model_dump()

    #
    # If we get to this point, settings.vector_store is defined, and there's a specific setting for this embedding.
    # settings.vector_store.base contains connection information, or may be undefined
    # settings.vector_store.<vector_name> contains the specific settings for this embedding
    #
    strategy = settings.embed_text.resolved_strategy(
        embeddings_llm_settings
    )  # get the default strategy
    strategy.update({
        "vector_store": {
            **(vector_store_params or {}),
            **(vector_store_settings),
        }
    })  # update the default strategy with the vector store settings
    # This ensures the vector store config is part of the strategy and not the global config
    return {
        "strategy": strategy,
    }
