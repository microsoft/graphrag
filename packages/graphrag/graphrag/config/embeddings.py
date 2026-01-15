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
