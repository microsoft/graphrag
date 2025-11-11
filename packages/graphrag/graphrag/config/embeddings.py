# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing embeddings values."""

entity_description_embedding = "entity_description"
community_full_content_embedding = "community_full_content"
text_unit_text_embedding = "text_unit_text"

all_embeddings: set[str] = {
    entity_description_embedding,
    community_full_content_embedding,
    text_unit_text_embedding,
}
default_embeddings: list[str] = [
    entity_description_embedding,
    community_full_content_embedding,
    text_unit_text_embedding,
]


def create_index_name(
    index_prefix: str, embedding_name: str, validate: bool = True
) -> str:
    """
    Create a index name for the embedding store.

    Within any given vector store, we can have multiple sets of embeddings organized into projects.
    The `container` param is used for this partitioning, and is added as a index_prefix to the index name for differentiation.

    The embedding name is fixed, with the available list defined in graphrag.index.config.embeddings

    Note that we use dot notation in our names, but many vector stores do not support this - so we convert to dashes.
    """
    if validate and embedding_name not in all_embeddings:
        msg = f"Invalid embedding name: {embedding_name}"
        raise KeyError(msg)

    if index_prefix:
        return f"{index_prefix}-{embedding_name}"
    return embedding_name
