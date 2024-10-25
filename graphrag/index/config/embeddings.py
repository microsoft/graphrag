# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing embeddings values."""

entity_name_embedding = "entity.name"
entity_description_embedding = "entity.description"
relationship_description_embedding = "relationship.description"
document_raw_content_embedding = "document.raw_content"
community_title_embedding = "community.title"
community_summary_embedding = "community.summary"
community_full_content_embedding = "community.full_content"
text_unit_text_embedding = "text_unit.text"

all_embeddings: set[str] = {
    entity_name_embedding,
    entity_description_embedding,
    relationship_description_embedding,
    document_raw_content_embedding,
    community_title_embedding,
    community_summary_embedding,
    community_full_content_embedding,
    text_unit_text_embedding,
}
required_embeddings: set[str] = {entity_description_embedding}
