# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

from . import _named


class CommunityReport(_named.Named):
    """Defines an LLM-generated summary report of a community."""

    community_id: str
    """The ID of the community this report is associated with."""

    summary: str = ""
    """Summary of the report."""

    full_content: str = ""
    """Full content of the report."""

    rank: float = 1.0
    """
    Rank of the report, used for sorting (optional). Higher means more 
    important.
    """

    summary_embedding: typing.Optional[typing.List[float]] = None
    """
    The semantic (i.e. text) embedding of the report summary (optional).
    """

    full_content_embedding: typing.Optional[typing.List[float]] = None
    """
    The semantic (i.e. text) embedding of the full report content (optional).
    """

    attributes: typing.Optional[typing.Dict[str, typing.Any]] = None
    """
    A dictionary of additional attributes associated with the report (optional).
    """
