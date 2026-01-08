# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""TextDocument dataclass."""

import logging
from dataclasses import dataclass
from typing import Any

from graphrag.index.input.get_property import get_property

logger = logging.getLogger(__name__)


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
    raw_data: dict[str, Any] | None = None
    """Raw data from source document."""

    def pluck_metadata(self, fields: list[str]) -> dict[str, Any]:
        """Extract metadata fields from a TextDocument.

        This takes a two step approach for flexibility:
        1. If the field is one of the standard text document fields (id, title, text, creation_date), just grab it directly. This accommodates unstructured text for example, which just has the standard fields.
        2. Otherwise. try to extract it from the raw_data dict. This allows users to specify any column from the original input file.

        If a field does not exist in either location, we'll throw because that means the user config is incorrect.
        """
        metadata = {}
        for field in fields:
            if field in ["id", "title", "text", "creation_date"]:
                value = getattr(self, field)
            else:
                raw = self.raw_data or {}
                value = get_property(raw, field)
                if value is None:
                    logger.warning(
                        "Metadata field '%s' not found in TextDocument standard fields or raw_data. Please check your configuration.",
                        field,
                    )
            if value is not None:
                metadata[field] = value
        return metadata
