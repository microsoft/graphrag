# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Module for preparing text-unit data and counting relationships for system prompts in the GraphRAG framework.

Functions:
    build_text_unit_context: Prepares text-unit data as context for system prompts.
    count_relationships: Counts the number of relationships associated with a text unit for a given entity.
"""

from __future__ import annotations

import random
import typing

import pandas as pd
import tiktoken

from ... import _model
from .... import _utils


def build_text_unit_context(
    text_units: typing.List[_model.TextUnit],
    token_encoder: typing.Optional[tiktoken.Encoding] = None,
    column_delimiter: str = "|",
    shuffle_data: bool = True,
    data_max_tokens: int = 8000,
    context_name: str = "Sources",
    random_state: int = 86,
) -> typing.Tuple[str, typing.Dict[str, pd.DataFrame]]:
    """
    Prepares text-unit data as a context table for use in system prompts.

    Args:
        text_units: A list of text units to include in the context.
        token_encoder: An optional token encoder to calculate token counts.
        column_delimiter:
            The delimiter to use for separating columns in the context data.
        shuffle_data:
            Whether to shuffle the text units before adding them to the context.
        data_max_tokens:
            The maximum number of tokens allowed in the context data.
        context_name: The name to use for the context section.
        random_state:
            A seed used to shuffle the text units (if shuffle_data is True).

    Returns:
        A tuple containing the formatted context string and a dictionary with
        the context data as a DataFrame.
    """
    if text_units is None or len(text_units) == 0:
        return "", {}

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
    current_tokens = _utils.num_tokens(current_context_text, token_encoder)
    all_context_records = [header]

    for unit in text_units:
        new_context = [
            unit.short_id or "",
            unit.text,
            *[
                str(unit.attributes.get(field, "")) if unit.attributes else ""
                for field in attribute_cols
            ],
        ]
        new_context_text = column_delimiter.join(new_context) + "\n"
        new_tokens = _utils.num_tokens(new_context_text, token_encoder)

        if current_tokens + new_tokens > data_max_tokens:
            break

        current_context_text += new_context_text
        all_context_records.append(new_context)
        current_tokens += new_tokens

    if len(all_context_records) > 1:
        record_df = pd.DataFrame(
            all_context_records[1:], columns=typing.cast(typing.Any, all_context_records[0])
        )
    else:
        record_df = pd.DataFrame()
    return current_context_text, {context_name.lower(): record_df}


def count_relationships(
    text_unit: _model.TextUnit, entity: _model.Entity, relationships: typing.Dict[str, _model.Relationship]
) -> int:
    """
    Counts the number of relationships associated with a text unit for a given
    entity.

    Args:
        text_unit: The text unit whose relationships will be counted.
        entity: The entity for which relationships will be checked.
        relationships: A dictionary of all relationships in the dataset.

    Returns:
        The number of relationships associated with the text unit for the given
        entity.
    """
    if text_unit.relationship_ids is None:
        entity_relationships = [
            rel for rel in relationships.values() if rel.source == entity.title or rel.target == entity.title
        ]
        entity_relationships = [
            rel for rel in entity_relationships if rel.text_unit_ids
        ]
        matching_relationships = [
            rel for rel in entity_relationships if text_unit.id in rel.text_unit_ids  # type: ignore
        ]  # type: ignore
    else:
        text_unit_relationships = [
            relationships[rel_id] for rel_id in text_unit.relationship_ids if rel_id in relationships
        ]
        matching_relationships = [
            rel for rel in text_unit_relationships if rel.source == entity.title or rel.target == entity.title
        ]
    return len(matching_relationships)
