# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the 'TextUnit' model."""

from dataclasses import dataclass
from typing import Any

from .identified import Identified


@dataclass
class TextUnit(Identified):
    """A protocol for a TextUnit item in a Document database."""

    text: str
    """The text of the unit."""

    text_embedding: list[float] | None = None
    """The text embedding for the text unit (optional)."""

    entity_ids: list[str] | None = None
    """List of entity IDs related to the text unit (optional)."""

    relationship_ids: list[str] | None = None
    """List of relationship IDs related to the text unit (optional)."""

    covariate_ids: dict[str, list[str]] | None = None
    "Dictionary of different types of covariates related to the text unit (optional)."

    n_tokens: int | None = None
    """The number of tokens in the text (optional)."""

    document_ids: list[str] | None = None
    """List of document IDs in which the text unit appears (optional)."""

    attributes: dict[str, Any] | None = None
    """A dictionary of additional attributes associated with the text unit (optional)."""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "short_id",
        text_key: str = "text",
        text_embedding_key: str = "text_embedding",
        entities_key: str = "entity_ids",
        relationships_key: str = "relationship_ids",
        covariates_key: str = "covariate_ids",
        n_tokens_key: str = "n_tokens",
        document_ids_key: str = "document_ids",
        attributes_key: str = "attributes",
    ) -> "TextUnit":
        """Create a new text unit from the dict data."""
        return TextUnit(
            id=d[id_key],
            short_id=d.get(short_id_key),
            text=d[text_key],
            text_embedding=d.get(text_embedding_key),
            entity_ids=d.get(entities_key),
            relationship_ids=d.get(relationships_key),
            covariate_ids=d.get(covariates_key),
            n_tokens=d.get(n_tokens_key),
            document_ids=d.get(document_ids_key),
            attributes=d.get(attributes_key),
        )
