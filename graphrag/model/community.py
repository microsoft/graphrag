# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the 'Community' model."""

from dataclasses import dataclass
from typing import Any

from .named import Named


@dataclass
class Community(Named):
    """A protocol for a community in the system."""

    level: str = ""
    """Community level."""

    entity_ids: list[str] | None = None
    """List of entity IDs related to the community (optional)."""

    relationship_ids: list[str] | None = None
    """List of relationship IDs related to the community (optional)."""

    covariate_ids: dict[str, list[str]] | None = None
    """Dictionary of different types of covariates related to the community (optional), e.g. claims"""

    attributes: dict[str, Any] | None = None
    """A dictionary of additional attributes associated with the community (optional). To be included in the search prompt."""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        title_key: str = "title",
        short_id_key: str = "short_id",
        level_key: str = "level",
        entities_key: str = "entity_ids",
        relationships_key: str = "relationship_ids",
        covariates_key: str = "covariate_ids",
        attributes_key: str = "attributes",
    ) -> "Community":
        """Create a new community from the dict data."""
        return Community(
            id=d[id_key],
            title=d[title_key],
            short_id=d.get(short_id_key),
            level=d[level_key],
            entity_ids=d.get(entities_key),
            relationship_ids=d.get(relationships_key),
            covariate_ids=d.get(covariates_key),
            attributes=d.get(attributes_key),
        )
