# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Orchestration Context Builders."""

from enum import Enum

from graphrag.model import Entity, Relationship
from graphrag.query.input.retrieval.entities import (
    get_entity_by_key,
    get_entity_by_name,
)
from graphrag.query.llm.base import BaseTextEmbedding
from graphrag.vector_stores import BaseVectorStore


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

def map_query_to_entities_in_place(
    query: str,
    text_embedding_vectorstore: BaseVectorStore,
    text_embedder: BaseTextEmbedding,
    k: int = 10,
    oversample_scaler: int = 2,
    preselected_entities=[]
) -> list[Entity]:
    """Extract entities that match a given query using semantic similarity of text embeddings of query and entity descriptions."""
    # get entities with highest semantic similarity to query
    # oversample to account for excluded entities
    search_results = text_embedding_vectorstore.get_extracted_entities(
        text=query,
        text_embedder=lambda t: text_embedder.embed(t),
        k=k * oversample_scaler,
        preselected_entities=preselected_entities
    )
    import ast
    for result in search_results:
        result.community_ids = ast.literal_eval(result.community_ids)
    return search_results

def map_query_to_entities(
    query: str,
    text_embedding_vectorstore: BaseVectorStore,
    text_embedder: BaseTextEmbedding,
    all_entities: list[Entity],
    embedding_vectorstore_key: str = EntityVectorStoreKey.ID,
    include_entity_names: list[str] | None = None,
    exclude_entity_names: list[str] | None = None,
    k: int = 10,
    oversample_scaler: int = 2,
    preselected_entities=[]
) -> list[Entity]:
    """Extract entities that match a given query using semantic similarity of text embeddings of query and entity descriptions."""
    if all_entities == []:
        return map_query_to_entities_in_place(
            query,
            text_embedding_vectorstore,
            text_embedder,
            k,
            oversample_scaler,
            preselected_entities=preselected_entities
        )

    if include_entity_names is None:
        include_entity_names = []
    if exclude_entity_names is None:
        exclude_entity_names = []
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


def find_nearest_neighbors_by_graph_embeddings(
    entity_id: str,
    graph_embedding_vectorstore: BaseVectorStore,
    all_entities: list[Entity],
    exclude_entity_names: list[str] | None = None,
    embedding_vectorstore_key: str = EntityVectorStoreKey.ID,
    k: int = 10,
    oversample_scaler: int = 2,
) -> list[Entity]:
    """Retrieve related entities by graph embeddings."""
    if exclude_entity_names is None:
        exclude_entity_names = []
    # find nearest neighbors of this entity using graph embedding
    query_entity = get_entity_by_key(
        entities=all_entities, key=embedding_vectorstore_key, value=entity_id
    )
    query_embedding = query_entity.graph_embedding if query_entity else None

    # oversample to account for excluded entities
    if query_embedding:
        matched_entities = []
        search_results = graph_embedding_vectorstore.similarity_search_by_vector(
            query_embedding=query_embedding, k=k * oversample_scaler
        )
        for result in search_results:
            matched = get_entity_by_key(
                entities=all_entities,
                key=embedding_vectorstore_key,
                value=result.document.id,
            )
            if matched:
                matched_entities.append(matched)

        # filter out excluded entities
        if exclude_entity_names:
            matched_entities = [
                entity
                for entity in matched_entities
                if entity.title not in exclude_entity_names
            ]
        matched_entities.sort(key=lambda x: x.rank, reverse=True)
        return matched_entities[:k]

    return []


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
