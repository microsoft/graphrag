# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

from . import _identified


class Relationship(_identified.Identified):
    """
    A relationship between two entities. This is a generic relationship, and
    can be used to represent any type of relationship between any two entities.
    """

    source: str = ""
    """The source entity name."""

    target: str = ""
    """The target entity name."""

    weight: float = 1.0
    """The edge weight."""

    description: typing.Optional[str] = None
    """A description of the relationship (optional)."""

    description_embedding: typing.Optional[typing.List[float]] = None
    """The semantic embedding for the relationship description (optional)."""

    text_unit_ids: typing.Optional[typing.List[str]] = None
    """List of text unit IDs in which the relationship appears (optional)."""

    document_ids: typing.Optional[typing.List[str]] = None
    """List of document IDs in which the relationship appears (optional)."""

    attributes: typing.Optional[typing.Dict[str, typing.Any]] = None
    """
    Additional attributes associated with the relationship (optional). To be 
    included in the search prompt
    """
