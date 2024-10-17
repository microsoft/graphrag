# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

from . import _named


class Document(_named.Named):
    """A protocol for a document in the system."""

    type: str = "text"
    """Type of the document."""

    text_unit_ids: typing.List[str] = []
    """list of text units in the document."""

    raw_content: str = ""
    """The raw text content of the document."""

    summary: typing.Optional[str] = None
    """Summary of the document (optional)."""

    summary_embedding: typing.Optional[typing.List[float]] = None
    """The semantic embedding for the document summary (optional)."""

    raw_content_embedding: typing.Optional[typing.List[float]] = None
    """The semantic embedding for the document raw content (optional)."""

    attributes: typing.Optional[typing.Dict[str, typing.Any]] = None
    """A dictionary of structured attributes such as author, etc (optional)."""
