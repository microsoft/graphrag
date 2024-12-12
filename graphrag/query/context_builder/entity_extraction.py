# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Orchestration Context Builders."""

from enum import Enum

from graphrag.model.entity import Entity
from graphrag.model.relationship import Relationship
from graphrag.query.input.retrieval.entities import (
    get_entity_by_id,
    get_entity_by_key,
    get_entity_by_name,
)
from graphrag.query.llm.base import BaseTextEmbedding
from graphrag.vector_stores.base import BaseVectorStore


class EntityVectorStoreKey(str, Enum):
    """Keys used as ids in the entity embedding vectorstores."""

    ID = "id"
    TITLE = "title"

    @staticmethod
    def from_string(value: str) -> "EntityVectorStoreKey":
        """Convert string to EntityVectorStoreKey."""
        if value == "id":
            return EntityVectorStoreKey.ID
        if value == "title":
            return EntityVectorStoreKey.TITLE

        msg = f"Invalid EntityVectorStoreKey: {value}"
        raise ValueError(msg)


def map_query_to_entities(
    query: str,
    text_embedding_vectorstore: BaseVectorStore,
    text_embedder: BaseTextEmbedding,
    all_entities_dict: dict[str, Entity],
    embedding_vectorstore_key: str = EntityVectorStoreKey.ID,
    include_entity_names: list[str] | None = None,
    exclude_entity_names: list[str] | None = None,
    k: int = 10,
    oversample_scaler: int = 2,
) -> list[Entity]:
    """Extract entities that match a given query using semantic similarity of text embeddings of query and entity descriptions."""
    if include_entity_names is None:
        include_entity_names = []
    if exclude_entity_names is None:
        exclude_entity_names = []
    all_entities = list(all_entities_dict.values())
    matched_entities = []
    if query != "":
        # get entities with highest semantic similarity to query
        # oversample to account for excluded entities
        search_results = text_embedding_vectorstore.similarity_search_by_text(
            text=query,
            text_embedder=lambda t: text_embedder.embed(t),
            k=k * oversample_scaler,
        )
        for result in search_results:
            if embedding_vectorstore_key == EntityVectorStoreKey.ID and isinstance(
                result.document.id, str
            ):
                matched = get_entity_by_id(all_entities_dict, result.document.id)
            else:
                matched = get_entity_by_key(
                    entities=all_entities,
                    key=embedding_vectorstore_key,
                    value=result.document.id,
                )
            if matched:
                matched_entities.append(matched)
    else:
        all_entities.sort(key=lambda x: x.rank if x.rank else 0, reverse=True)
        matched_entities = all_entities[:k]

    # filter out excluded entities
    if exclude_entity_names:
        matched_entities = [
            entity
            for entity in matched_entities
            if entity.title not in exclude_entity_names
        ]

    # add entities in the include_entity list
    included_entities = []
    for entity_name in include_entity_names:
        included_entities.extend(get_entity_by_name(all_entities, entity_name))
    return included_entities + matched_entities


def find_nearest_neighbors_by_entity_rank(
    entity_name: str,
    all_entities: list[Entity],
    all_relationships: list[Relationship],
    exclude_entity_names: list[str] | None = None,
    k: int | None = 10,
) -> list[Entity]:
    """Retrieve entities that have direct connections with the target entity, sorted by entity rank."""
    if exclude_entity_names is None:
        exclude_entity_names = []
    entity_relationships = [
        rel
        for rel in all_relationships
        if rel.source == entity_name or rel.target == entity_name
    ]
    source_entity_names = {rel.source for rel in entity_relationships}
    target_entity_names = {rel.target for rel in entity_relationships}
    related_entity_names = (source_entity_names.union(target_entity_names)).difference(
        set(exclude_entity_names)
    )
    top_relations = [
        entity for entity in all_entities if entity.title in related_entity_names
    ]
    top_relations.sort(key=lambda x: x.rank if x.rank else 0, reverse=True)
    if k:
        return top_relations[:k]
    return top_relations
