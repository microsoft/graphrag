# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the 'Node' model."""

from dataclasses import dataclass
from typing import Any

from .named import Named


@dataclass
class Node(Named):
    """A protocol for a node in the system."""

    community_id: str = ""
    """The ID of the community this report is associated with."""

    level: str = ""
    """Community level."""

    title: str = ""
    """Title of the node."""

    human_readable_id: str | None = None
    """Human readable ID of the node (optional)."""

    type: str | None = None
    """Type of the node (can be any string, optional)."""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "human_readable_id",
        title_key: str = "title",
        community_id_key: str = "community",
        level_key: str = "level",
        type_key: str = "type",
    ) -> "Node":
        """Create a new node from the dict data."""
        return Node(
            id=d[id_key],
            title=d[title_key],
            short_id=d.get(short_id_key),
            community_id=d[community_id_key],
            level=d[level_key],
            type=d.get(type_key),
        )
