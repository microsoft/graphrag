# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

import pandas as pd

from ... import _model


def get_candidate_text_units(
    selected_entities: typing.List[_model.Entity],
    text_units: typing.List[_model.TextUnit],
) -> pd.DataFrame:
    """Get all text units that are associated to selected entities."""
    selected_text_ids_ = [
        entity.text_unit_ids for entity in selected_entities if entity.text_unit_ids
    ]
    selected_text_ids = [item for sublist in selected_text_ids_ for item in sublist]
    selected_text_units = [unit for unit in text_units if unit.id in selected_text_ids]
    return to_text_unit_dataframe(selected_text_units)


def to_text_unit_dataframe(text_units: typing.List[_model.TextUnit]) -> pd.DataFrame:
    """Convert a list of text units to a pandas dataframe."""
    if len(text_units) == 0:
        return pd.DataFrame()

    # add header
    header = ["id", "text"]
    attribute_cols = (
        list(text_units[0].attributes.keys()) if text_units[0].attributes else []
    )
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    records = []
    for unit in text_units:
        new_record = [
            unit.short_id,
            unit.text,
            *[
                str(unit.attributes.get(field, ""))
                if unit.attributes and unit.attributes.get(field)
                else ""
                for field in attribute_cols
            ],
        ]
        records.append(new_record)
    return pd.DataFrame(records, columns=typing.cast(typing.Any, header))
