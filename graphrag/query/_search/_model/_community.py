# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

from . import _named


class Community(_named.Named):
    """A protocol for a community in the system."""

    level: str = ""
    """Community level."""

    entity_ids: typing.Optional[typing.List[str]] = None
    """typing.List of entity IDs related to the community (optional)."""

    relationship_ids: typing.Optional[typing.List[str]] = None
    """typing.List of relationship IDs related to the community (optional)."""

    covariate_ids: typing.Optional[typing.Dict[str, typing.List[str]]] = None
    """
    typing.Dictionary of different types of covariates related to the community 
    (optional), e.g. claims
    """

    attributes: typing.Optional[typing.Dict[str, typing.Any]] = None
    """
    A dictionary of additional attributes associated with the community 
    (optional). To be included in the search prompt.
    """
