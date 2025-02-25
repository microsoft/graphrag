# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the 'Relationship' model."""

from dataclasses import dataclass
from typing import Any

from graphrag.data_model.identified import Identified


@dataclass
class Relationship(Identified):
    """A relationship between two entities. This is a generic relationship, and can be used to represent any type of relationship between any two entities."""

    source: str
    """The source entity name."""

    target: str
    """The target entity name."""

    weight: float | None = 1.0
    """The edge weight."""

    description: str | None = None
    """A description of the relationship (optional)."""

    description_embedding: list[float] | None = None
    """The semantic embedding for the relationship description (optional)."""

    text_unit_ids: list[str] | None = None
    """List of text unit IDs in which the relationship appears (optional)."""

    rank: int | None = 1
    """Rank of the relationship, used for sorting (optional). Higher rank indicates more important relationship. This can be based on centrality or other metrics."""

    attributes: dict[str, Any] | None = None
    """Additional attributes associated with the relationship (optional). To be included in the search prompt"""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "human_readable_id",
        source_key: str = "source",
        target_key: str = "target",
        description_key: str = "description",
        rank_key: str = "rank",
        weight_key: str = "weight",
        text_unit_ids_key: str = "text_unit_ids",
        attributes_key: str = "attributes",
    ) -> "Relationship":
        """Create a new relationship from the dict data."""
        return Relationship(
            id=d[id_key],
            short_id=d.get(short_id_key),
            source=d[source_key],
            target=d[target_key],
            rank=d.get(rank_key, 1),
            description=d.get(description_key),
            weight=d.get(weight_key, 1.0),
            text_unit_ids=d.get(text_unit_ids_key),
            attributes=d.get(attributes_key),
        )
