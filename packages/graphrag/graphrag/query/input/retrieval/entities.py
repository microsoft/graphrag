# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Util functions to get entities from a collection."""

import uuid
from collections.abc import Iterable
from typing import Any, cast

import pandas as pd

from graphrag.data_model.entity import Entity


def get_entity_by_id(entities: dict[str, Entity], value: str) -> Entity | None:
    """Get entity by id."""
    entity = entities.get(value)
    if entity is None and is_valid_uuid(value):
        entity = entities.get(value.replace("-", ""))
    return entity


def get_entity_by_key(
    entities: Iterable[Entity], key: str, value: str | int
) -> Entity | None:
    """Get entity by key."""
    if isinstance(value, str) and is_valid_uuid(value):
        value_no_dashes = value.replace("-", "")
        for entity in entities:
            entity_value = getattr(entity, key)
            if entity_value in (value, value_no_dashes):
                return entity
    else:
        for entity in entities:
            if getattr(entity, key) == value:
                return entity
    return None


def get_entity_by_name(entities: Iterable[Entity], entity_name: str) -> list[Entity]:
    """Get entities by name."""
    return [entity for entity in entities if entity.title == entity_name]


def get_entity_by_attribute(
    entities: Iterable[Entity], attribute_name: str, attribute_value: Any
) -> list[Entity]:
    """Get entities by attribute."""
    return [
        entity
        for entity in entities
        if entity.attributes
        and entity.attributes.get(attribute_name) == attribute_value
    ]


def to_entity_dataframe(
    entities: list[Entity],
    include_entity_rank: bool = True,
    rank_description: str = "number of relationships",
) -> pd.DataFrame:
    """Convert a list of entities to a pandas dataframe."""
    if len(entities) == 0:
        return pd.DataFrame()
    header = ["id", "entity", "description"]
    if include_entity_rank:
        header.append(rank_description)
    attribute_cols = (
        list(entities[0].attributes.keys()) if entities[0].attributes else []
    )
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
    return pd.DataFrame(records, columns=cast("Any", header))


def is_valid_uuid(value: str) -> bool:
    """Determine if a string is a valid UUID."""
    try:
        uuid.UUID(str(value))
    except ValueError:
        return False
    else:
        return True
