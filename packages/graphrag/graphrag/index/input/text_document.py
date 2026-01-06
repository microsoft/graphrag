# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""TextDocument dataclass."""

from dataclasses import dataclass
from typing import Any


@dataclass
class TextDocument:
    """The TextDocument holds relevant content for GraphRAG indexing."""

    id: str
    """Unique identifier for the document."""
    text: str
    """The main text content of the document."""
    title: str
    """The title of the document."""
    creation_date: str
    """The creation date of the document, ISO-8601 format."""
    metadata: dict[str, Any] | None = None
    """Additional metadata associated with the document."""
