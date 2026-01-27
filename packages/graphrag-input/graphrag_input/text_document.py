# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""TextDocument dataclass."""

import logging
from dataclasses import dataclass
from typing import Any

from graphrag_input.get_property import get_property

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

    def get(self, field: str, default_value: Any = None) -> Any:
        """
        Get a single field from the TextDocument.

        Functions like the get method on a dictionary, returning default_value if the field is not found.

        Supports nested fields using dot notation.

        This takes a two step approach for flexibility:
        1. If the field is one of the standard text document fields (id, title, text, creation_date), just grab it directly. This accommodates unstructured text for example, which just has the standard fields.
        2. Otherwise. try to extract it from the raw_data dict. This allows users to specify any column from the original input file.

        """
        if field in ["id", "title", "text", "creation_date"]:
            return getattr(self, field)

        raw = self.raw_data or {}
        try:
            return get_property(raw, field)
        except KeyError:
            return default_value

    def collect(self, fields: list[str]) -> dict[str, Any]:
        """Extract data fields from a TextDocument into a dict."""
        data = {}
        for field in fields:
            value = self.get(field)
            if value is not None:
                data[field] = value
        return data
