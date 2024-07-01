# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the 'Entity' model."""

from dataclasses import dataclass
from typing import Any

from .named import Named


@dataclass
class Entity(Named):
    """A protocol for an entity in the system."""

    type: str | None = None
    """Type of the entity (can be any string, optional)."""

    description: str | None = None
    """Description of the entity (optional)."""

    description_embedding: list[float] | None = None
    """The semantic (i.e. text) embedding of the entity (optional)."""

    name_embedding: list[float] | None = None
    """The semantic (i.e. text) embedding of the entity (optional)."""

    graph_embedding: list[float] | None = None
    """The graph embedding of the entity, likely from node2vec (optional)."""

    community_ids: list[str] | None = None
    """The community IDs of the entity (optional)."""

    text_unit_ids: list[str] | None = None
    """List of text unit IDs in which the entity appears (optional)."""

    document_ids: list[str] | None = None
    """List of document IDs in which the entity appears (optional)."""

    rank: int | None = 1
    """Rank of the entity, used for sorting (optional). Higher rank indicates more important entity. This can be based on centrality or other metrics."""

    attributes: dict[str, Any] | None = None
    """Additional attributes associated with the entity (optional), e.g. start time, end time, etc. To be included in the search prompt."""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "short_id",
        title_key: str = "title",
        type_key: str = "type",
        description_key: str = "description",
        description_embedding_key: str = "description_embedding",
        name_embedding_key: str = "name_embedding",
        graph_embedding_key: str = "graph_embedding",
        community_key: str = "community",
        text_unit_ids_key: str = "text_unit_ids",
        document_ids_key: str = "document_ids",
        rank_key: str = "degree",
        attributes_key: str = "attributes",
    ) -> "Entity":
        """Create a new entity from the dict data."""
        return Entity(
            id=d[id_key],
            title=d[title_key],
            short_id=d.get(short_id_key),
            type=d.get(type_key),
            description=d.get(description_key),
            name_embedding=d.get(name_embedding_key),
            description_embedding=d.get(description_embedding_key),
            graph_embedding=d.get(graph_embedding_key),
            community_ids=d.get(community_key),
            rank=d.get(rank_key, 1),
            text_unit_ids=d.get(text_unit_ids_key),
            document_ids=d.get(document_ids_key),
            attributes=d.get(attributes_key),
        )
