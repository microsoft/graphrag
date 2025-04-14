# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Context Build utility methods."""

import random
from typing import Any, cast

import pandas as pd
import tiktoken

from graphrag.data_model.relationship import Relationship
from graphrag.data_model.text_unit import TextUnit
from graphrag.query.llm.text_utils import num_tokens

"""
Contain util functions to build text unit context for the search's system prompt
"""


def build_text_unit_context(
    text_units: list[TextUnit],
    token_encoder: tiktoken.Encoding | None = None,
    column_delimiter: str = "|",
    shuffle_data: bool = True,
    max_context_tokens: int = 8000,
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

        if current_tokens + new_tokens > max_context_tokens:
            break

        current_context_text += new_context_text
        all_context_records.append(new_context)
        current_tokens += new_tokens

    if len(all_context_records) > 1:
        record_df = pd.DataFrame(
            all_context_records[1:], columns=cast("Any", all_context_records[0])
        )
    else:
        record_df = pd.DataFrame()
    return current_context_text, {context_name.lower(): record_df}


def count_relationships(
    entity_relationships: list[Relationship], text_unit: TextUnit
) -> int:
    """Count the number of relationships of the selected entity that are associated with the text unit."""
    if not text_unit.relationship_ids:
        # Use list comprehension to count relationships where the text_unit.id is in rel.text_unit_ids
        return sum(
            1
            for rel in entity_relationships
            if rel.text_unit_ids and text_unit.id in rel.text_unit_ids
        )

    # Use a set for faster lookups if entity_relationships is large
    entity_relationship_ids = {rel.id for rel in entity_relationships}

    # Count matching relationship ids efficiently
    return sum(
        1 for rel_id in text_unit.relationship_ids if rel_id in entity_relationship_ids
    )
