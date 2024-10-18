# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

from . import _named


class Entity(_named.Named):
    """A protocol for an entity in the system."""

    type: typing.Optional[str] = None
    """Type of the entity (can be any string, optional)."""

    description: typing.Optional[str] = None
    """Description of the entity (optional)."""

    description_embedding: typing.Optional[typing.List[float]] = None
    """The semantic (i.e. text) embedding of the entity (optional)."""

    name_embedding: typing.Optional[typing.List[float]] = None
    """The semantic (i.e. text) embedding of the entity (optional)."""

    graph_embedding: typing.Optional[typing.List[float]] = None
    """The graph embedding of the entity, likely from node2vec (optional)."""

    community_ids: typing.Optional[typing.List[str]] = None
    """The community IDs of the entity (optional)."""

    text_unit_ids: typing.Optional[typing.List[str]] = None
    """List of text unit IDs in which the entity appears (optional)."""

    document_ids: typing.Optional[typing.List[str]] = None
    """List of document IDs in which the entity appears (optional)."""

    rank: int = 1
    """
    Rank of the entity, used for sorting (optional). Higher rank indicates more 
    important entity. This can be based on centrality or other metrics.
    """

    attributes: typing.Optional[typing.Dict[str, typing.Any]] = None
    """
    Additional attributes associated with the entity (optional), e.g. start 
    time, end time, etc. To be included in the search prompt.
    """
