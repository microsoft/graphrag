# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Context Build utility methods."""

import random
from typing import Any, cast

import pandas as pd
import tiktoken

from graphrag.model import Entity, Relationship, TextUnit
from graphrag.query.llm.text_utils import num_tokens

"""
Contain util functions to build text unit context for the search's system prompt
"""


def build_text_unit_context(
    text_units: list[TextUnit],
    token_encoder: tiktoken.Encoding | None = None,
    column_delimiter: str = "|",
    shuffle_data: bool = True,
    max_tokens: int = 8000,
    context_name: str = "Sources",
    random_state: int = 86,
) -> tuple[str, dict[str, pd.DataFrame]]:
    """Prepare text-unit data table as context data for system prompt."""
    if text_units is None or len(text_units) == 0:
        return ("", {})

    if shuffle_data:
        random.seed(random_state)
        random.shuffle(text_units)

    # add context header
    current_context_text = f"-----{context_name}-----" + "\n"

    # add header
    header = ["id", "text"]
    attribute_cols = (
        list(text_units[0].attributes.keys()) if text_units[0].attributes else []
    )
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    current_context_text += column_delimiter.join(header) + "\n"
    current_tokens = num_tokens(current_context_text, token_encoder)
    all_context_records = [header]

    for unit in text_units:
        new_context = [
            unit.short_id,
            unit.text,
            *[
                str(unit.attributes.get(field, "")) if unit.attributes else ""
                for field in attribute_cols
            ],
        ]
        new_context_text = column_delimiter.join(new_context) + "\n"
        new_tokens = num_tokens(new_context_text, token_encoder)

        if current_tokens + new_tokens > max_tokens:
            break

        current_context_text += new_context_text
        all_context_records.append(new_context)
        current_tokens += new_tokens

    if len(all_context_records) > 1:
        record_df = pd.DataFrame(
            all_context_records[1:], columns=cast(Any, all_context_records[0])
        )
    else:
        record_df = pd.DataFrame()
    return current_context_text, {context_name.lower(): record_df}


def count_relationships(
    text_unit: TextUnit, entity: Entity, relationships: dict[str, Relationship]
) -> int:
    """Count the number of relationships of the selected entity that are associated with the text unit."""
    matching_relationships = list[Relationship]()
    if text_unit.relationship_ids is None:
        entity_relationships = [
            rel
            for rel in relationships.values()
            if rel.source == entity.title or rel.target == entity.title
        ]
        entity_relationships = [
            rel for rel in entity_relationships if rel.text_unit_ids
        ]
        matching_relationships = [
            rel
            for rel in entity_relationships
            if text_unit.id in rel.text_unit_ids  # type: ignore
        ]  # type: ignore
    else:
        text_unit_relationships = [
            relationships[rel_id]
            for rel_id in text_unit.relationship_ids
            if rel_id in relationships
        ]
        matching_relationships = [
            rel
            for rel in text_unit_relationships
            if rel.source == entity.title or rel.target == entity.title
        ]
    return len(matching_relationships)
