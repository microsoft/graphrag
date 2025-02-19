# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the 'Document' model."""

from dataclasses import dataclass, field
from typing import Any

from graphrag.data_model.named import Named


@dataclass
class Document(Named):
    """A protocol for a document in the system."""

    type: str = "text"
    """Type of the document."""

    text_unit_ids: list[str] = field(default_factory=list)
    """list of text units in the document."""

    text: str = ""
    """The raw text content of the document."""

    attributes: dict[str, Any] | None = None
    """A dictionary of structured attributes such as author, etc (optional)."""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "human_readable_id",
        title_key: str = "title",
        type_key: str = "type",
        text_key: str = "text",
        text_units_key: str = "text_units",
        attributes_key: str = "attributes",
    ) -> "Document":
        """Create a new document from the dict data."""
        return Document(
            id=d[id_key],
            short_id=d.get(short_id_key),
            title=d[title_key],
            type=d.get(type_key, "text"),
            text=d[text_key],
            text_unit_ids=d.get(text_units_key, []),
            attributes=d.get(attributes_key),
        )
