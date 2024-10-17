# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import typing

from . import _identified


class TextUnit(_identified.Identified):
    """A protocol for a TextUnit item in a Document database."""

    text: str = ""
    """The text of the unit."""

    text_embedding: typing.Optional[typing.List[float]] = None
    """The text embedding for the text unit (optional)."""

    entity_ids: typing.Optional[typing.List[str]] = None
    """List of entity IDs related to the text unit (optional)."""

    relationship_ids: typing.Optional[typing.List[str]] = None
    """List of relationship IDs related to the text unit (optional)."""

    covariate_ids: typing.Optional[typing.Dict[str, typing.List[str]]] = None
    """
    Dictionary of different types of covariates related to the text unit 
    (optional).
    """

    n_tokens: typing.Optional[int] = None
    """The number of tokens in the text (optional)."""

    document_ids: typing.Optional[typing.List[str]] = None
    """List of document IDs in which the text unit appears (optional)."""

    attributes: typing.Optional[typing.Dict[str, typing.Any]] = None
    """
    A dictionary of additional attributes associated with the text unit
    (optional).
    """
