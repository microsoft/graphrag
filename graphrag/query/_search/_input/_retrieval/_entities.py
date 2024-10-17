# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import uuid
import typing

import pandas as pd

from ... import _model


def get_entity_by_key(
    entities: typing.Iterable[_model.Entity], key: str, value: str | int
) -> typing.Optional[_model.Entity]:
    """Get entity by key."""
    for entity in entities:
        if isinstance(value, str) and is_valid_uuid(value):
            if getattr(entity, key) == value or getattr(entity, key) == value.replace("-", ""):
                return entity
        else:
            if getattr(entity, key) == value:
                return entity
    return None


def get_entity_by_name(entities: typing.Iterable[_model.Entity], entity_name: str) -> typing.List[_model.Entity]:
    """Get entities by name."""
    return [entity for entity in entities if entity.title == entity_name]


def get_entity_by_attribute(
    entities: typing.Iterable[_model.Entity], attribute_name: str, attribute_value: typing.Any
) -> typing.List[_model.Entity]:
    """Get entities by attribute."""
    return [
        entity for entity in entities
        if entity.attributes and entity.attributes.get(attribute_name) == attribute_value
    ]


def to_entity_dataframe(
    entities: typing.List[_model.Entity],
    include_entity_rank: bool = True,
    rank_description: str = "number of relationships",
) -> pd.DataFrame:
    """Convert a list of entities to a pandas dataframe."""
    if len(entities) == 0:
        return pd.DataFrame()
    header = ["id", "entity", "description"]
    if include_entity_rank:
        header.append(rank_description)
    attribute_cols = (list(entities[0].attributes.keys()) if entities[0].attributes else [])
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    records = []
    for entity in entities:
        new_record = [
            entity.short_id if entity.short_id else "",
            entity.title,
            entity.description if entity.description else "",
        ]
        if include_entity_rank:
            new_record.append(str(entity.rank))

        for field in attribute_cols:
            field_value = (
                str(entity.attributes.get(field))
                if entity.attributes and entity.attributes.get(field)
                else ""
            )
            new_record.append(field_value)
        records.append(new_record)
    return pd.DataFrame(records, columns=typing.cast(typing.Any, header))


def is_valid_uuid(value: str) -> bool:
    """Determine if a string is a valid UUID."""
    try:
        uuid.UUID(str(value))
    except ValueError:
        return False
    else:
        return True
