# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing embeddings values."""

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
default_embeddings: list[str] = [
    entity_description_embedding,
    community_full_content_embedding,
    text_unit_text_embedding,
]


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
