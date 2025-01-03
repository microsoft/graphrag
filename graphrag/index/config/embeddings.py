# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing embeddings values."""

from graphrag.config.enums import TextEmbeddingTarget
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.text_embedding_config import TextEmbeddingConfig

entity_title_embedding = "entity.title"
entity_description_embedding = "entity.description"
relationship_description_embedding = "relationship.description"
document_text_embedding = "document.text"
community_title_embedding = "community.title"
community_summary_embedding = "community.summary"
community_full_content_embedding = "community.full_content"
text_unit_text_embedding = "text_unit.text"

all_embeddings: set[str] = {
    entity_title_embedding,
    entity_description_embedding,
    relationship_description_embedding,
    document_text_embedding,
    community_title_embedding,
    community_summary_embedding,
    community_full_content_embedding,
    text_unit_text_embedding,
}
required_embeddings: set[str] = {
    entity_description_embedding,
    community_full_content_embedding,
    text_unit_text_embedding,
}


def get_embedded_fields(settings: GraphRagConfig) -> set[str]:
    """Get the fields to embed based on the enum or specifically skipped embeddings."""
    match settings.embeddings.target:
        case TextEmbeddingTarget.all:
            return all_embeddings.difference(settings.embeddings.skip)
        case TextEmbeddingTarget.required:
            return required_embeddings
        case TextEmbeddingTarget.none:
            return set()
        case _:
            msg = f"Unknown embeddings target: {settings.embeddings.target}"
            raise ValueError(msg)


def get_embedding_settings(
    settings: TextEmbeddingConfig,
    vector_store_params: dict | None = None,
) -> dict:
    """Transform GraphRAG config into settings for workflows."""
    # TEMP
    vector_store_settings = settings.vector_store
    if vector_store_settings is None:
        return {"strategy": settings.resolved_strategy()}
    #
    # If we get to this point, settings.vector_store is defined, and there's a specific setting for this embedding.
    # settings.vector_store.base contains connection information, or may be undefined
    # settings.vector_store.<vector_name> contains the specific settings for this embedding
    #
    strategy = settings.resolved_strategy()  # get the default strategy
    strategy.update({
        "vector_store": {**(vector_store_params or {}), **vector_store_settings}
    })  # update the default strategy with the vector store settings
    # This ensures the vector store config is part of the strategy and not the global config
    return {
        "strategy": strategy,
    }
