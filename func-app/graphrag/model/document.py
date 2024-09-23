# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the 'Document' model."""

from dataclasses import dataclass, field
from typing import Any

from .named import Named


@dataclass
class Document(Named):
    """A protocol for a document in the system."""

    type: str = "text"
    """Type of the document."""

    text_unit_ids: list[str] = field(default_factory=list)
    """list of text units in the document."""

    raw_content: str = ""
    """The raw text content of the document."""

    summary: str | None = None
    """Summary of the document (optional)."""

    summary_embedding: list[float] | None = None
    """The semantic embedding for the document summary (optional)."""

    raw_content_embedding: list[float] | None = None
    """The semantic embedding for the document raw content (optional)."""

    attributes: dict[str, Any] | None = None
    """A dictionary of structured attributes such as author, etc (optional)."""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "short_id",
        title_key: str = "title",
        type_key: str = "type",
        raw_content_key: str = "raw_content",
        summary_key: str = "summary",
        summary_embedding_key: str = "summary_embedding",
        raw_content_embedding_key: str = "raw_content_embedding",
        text_units_key: str = "text_units",
        attributes_key: str = "attributes",
    ) -> "Document":
        """Create a new document from the dict data."""
        return Document(
            id=d[id_key],
            short_id=d.get(short_id_key),
            title=d[title_key],
            type=d.get(type_key, "text"),
            raw_content=d[raw_content_key],
            summary=d.get(summary_key),
            summary_embedding=d.get(summary_embedding_key),
            raw_content_embedding=d.get(raw_content_embedding_key),
            text_unit_ids=d.get(text_units_key, []),
            attributes=d.get(attributes_key),
        )
