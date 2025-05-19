# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the 'Community' model."""

from dataclasses import dataclass
from typing import Any

from graphrag.data_model.named import Named


@dataclass
class Community(Named):
    """A protocol for a community in the system."""

    level: str
    """Community level."""

    parent: str
    """Community ID of the parent node of this community."""

    children: list[str]
    """List of community IDs of the child nodes of this community."""

    entity_ids: list[str] | None = None
    """List of entity IDs related to the community (optional)."""

    relationship_ids: list[str] | None = None
    """List of relationship IDs related to the community (optional)."""

    text_unit_ids: list[str] | None = None
    """List of text unit IDs related to the community (optional)."""

    covariate_ids: dict[str, list[str]] | None = None
    """Dictionary of different types of covariates related to the community (optional), e.g. claims"""

    attributes: dict[str, Any] | None = None
    """A dictionary of additional attributes associated with the community (optional). To be included in the search prompt."""

    size: int | None = None
    """The size of the community (Amount of text units)."""

    period: str | None = None
    ""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        title_key: str = "title",
        short_id_key: str = "human_readable_id",
        level_key: str = "level",
        entities_key: str = "entity_ids",
        relationships_key: str = "relationship_ids",
        text_units_key: str = "text_unit_ids",
        covariates_key: str = "covariate_ids",
        parent_key: str = "parent",
        children_key: str = "children",
        attributes_key: str = "attributes",
        size_key: str = "size",
        period_key: str = "period",
    ) -> "Community":
        """Create a new community from the dict data."""
        return Community(
            id=d[id_key],
            title=d[title_key],
            level=d[level_key],
            parent=d[parent_key],
            children=d[children_key],
            short_id=d.get(short_id_key),
            entity_ids=d.get(entities_key),
            relationship_ids=d.get(relationships_key),
            text_unit_ids=d.get(text_units_key),
            covariate_ids=d.get(covariates_key),
            attributes=d.get(attributes_key),
            size=d.get(size_key),
            period=d.get(period_key),
        )
