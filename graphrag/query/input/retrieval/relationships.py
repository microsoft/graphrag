# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Util functions to retrieve relationships from a collection."""

import time
from typing import Any, cast

import pandas as pd

from common.graph_db_client import GraphDBClient
from graphrag.model import Entity, Relationship

from graphrag.query.input.loaders.dfs import read_relationships

def get_relationships_from_graphdb(query:str,selected_entity_names:list[str],graphdb_client: GraphDBClient):
    relationships_result=graphdb_client._client.submit(
        message=query,
        bindings={
            "prop_selected_entity_names": selected_entity_names,
        }
    )
    time.sleep(5)
    print(graphdb_client.result_to_df(relationships_result))
    return read_relationships(
        graphdb_client.result_to_df(relationships_result),
        short_id_col="human_readable_id"
    )

def get_in_network_relationships(
    selected_entities: list[Entity],
    relationships: list[Relationship],
    ranking_attribute: str = "rank",
    graphdb_client: GraphDBClient|None=None,
) -> list[Relationship]:
    """Get all directed relationships between selected entities, sorted by ranking_attribute."""
    selected_entity_names = [entity.title for entity in selected_entities]
    if not graphdb_client:
        selected_relationships = [
            relationship
            for relationship in relationships
            if relationship.source in selected_entity_names
            and relationship.target in selected_entity_names
        ]
    else:
        selected_relationships = get_relationships_from_graphdb(
            query=(
                "g.E()"
                ".where(inV().has('name',within(prop_selected_entity_names)))"
                ".where(outV().has('name',within(prop_selected_entity_names)))"
            ),
            selected_entity_names=selected_entity_names,
            graphdb_client=graphdb_client
        )
    if len(selected_relationships) <= 1:
        return selected_relationships

    # sort by ranking attribute
    return sort_relationships_by_ranking_attribute(
        selected_relationships, selected_entities, ranking_attribute
    )


def get_out_network_relationships(
    selected_entities: list[Entity],
    relationships: list[Relationship],
    ranking_attribute: str = "rank",
    graphdb_client: GraphDBClient|None=None,
) -> list[Relationship]:
    """Get relationships from selected entities to other entities that are not within the selected entities, sorted by ranking_attribute."""
    selected_entity_names = [entity.title for entity in selected_entities]
    if not graphdb_client:
        source_relationships = [
            relationship
            for relationship in relationships
            if relationship.source in selected_entity_names
            and relationship.target not in selected_entity_names
        ]
        target_relationships = [
            relationship
            for relationship in relationships
            if relationship.target in selected_entity_names
            and relationship.source not in selected_entity_names
        ]
        selected_relationships = source_relationships + target_relationships
    else:
        selected_relationships = get_relationships_from_graphdb(
            query=(
                "g.E().union("
                "__.where(outV().has('name',without(prop_selected_entity_names)))"
                ".where(inV().has('name',within(prop_selected_entity_names))),"
                "__.where(inV().has('name',without(prop_selected_entity_names)))"
                ".where(outV().has('name',within(prop_selected_entity_names)))"
                ")"
            ),
            selected_entity_names= selected_entity_names,
            graphdb_client=graphdb_client
        )
    return sort_relationships_by_ranking_attribute(
        selected_relationships, selected_entities, ranking_attribute
    )


def get_candidate_relationships(
    selected_entities: list[Entity],
    relationships: list[Relationship],
) -> list[Relationship]:
    """Get all relationships that are associated with the selected entities."""
    selected_entity_names = [entity.title for entity in selected_entities]
    return [
        relationship
        for relationship in relationships
        if relationship.source in selected_entity_names
        or relationship.target in selected_entity_names
    ]


def get_entities_from_relationships(
    relationships: list[Relationship], entities: list[Entity]
) -> list[Entity]:
    """Get all entities that are associated with the selected relationships."""
    selected_entity_names = [relationship.source for relationship in relationships] + [
        relationship.target for relationship in relationships
    ]
    return [entity for entity in entities if entity.title in selected_entity_names]


def calculate_relationship_combined_rank(
    relationships: list[Relationship],
    entities: list[Entity],
    ranking_attribute: str = "rank",
) -> list[Relationship]:
    """Calculate default rank for a relationship based on the combined rank of source and target entities."""
    entity_mappings = {entity.title: entity for entity in entities}

    for relationship in relationships:
        if relationship.attributes is None:
            relationship.attributes = {}
        source = entity_mappings.get(relationship.source)
        target = entity_mappings.get(relationship.target)
        source_rank = source.rank if source and source.rank else 0
        target_rank = target.rank if target and target.rank else 0
        relationship.attributes[ranking_attribute] = source_rank + target_rank  # type: ignore
    return relationships


def sort_relationships_by_ranking_attribute(
    relationships: list[Relationship],
    entities: list[Entity],
    ranking_attribute: str = "rank",
) -> list[Relationship]:
    """
    Sort relationships by a ranking_attribute.

    If no ranking attribute exists, sort by combined rank of source and target entities.
    """
    if len(relationships) == 0:
        return relationships

    # sort by ranking attribute
    attribute_names = (
        list(relationships[0].attributes.keys()) if relationships[0].attributes else []
    )
    if ranking_attribute in attribute_names:
        relationships.sort(
            key=lambda x: int(x.attributes[ranking_attribute]) if x.attributes else 0,
            reverse=True,
        )
    elif ranking_attribute == "weight":
        relationships.sort(key=lambda x: x.weight if x.weight else 0.0, reverse=True)
    else:
        # ranking attribute do not exist, calculate rank = combined ranks of source and target
        relationships = calculate_relationship_combined_rank(
            relationships, entities, ranking_attribute
        )
        relationships.sort(
            key=lambda x: int(x.attributes[ranking_attribute]) if x.attributes else 0,
            reverse=True,
        )
    return relationships


def to_relationship_dataframe(
    relationships: list[Relationship], include_relationship_weight: bool = True
) -> pd.DataFrame:
    """Convert a list of relationships to a pandas dataframe."""
    if len(relationships) == 0:
        return pd.DataFrame()

    header = ["id", "source", "target", "description"]
    if include_relationship_weight:
        header.append("weight")
    attribute_cols = (
        list(relationships[0].attributes.keys()) if relationships[0].attributes else []
    )
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    records = []
    for rel in relationships:
        new_record = [
            rel.short_id if rel.short_id else "",
            rel.source,
            rel.target,
            rel.description if rel.description else "",
        ]
        if include_relationship_weight:
            new_record.append(str(rel.weight if rel.weight else ""))
        for field in attribute_cols:
            field_value = (
                str(rel.attributes.get(field))
                if rel.attributes and rel.attributes.get(field)
                else ""
            )
            new_record.append(field_value)
        records.append(new_record)
    return pd.DataFrame(records, columns=cast(Any, header))
