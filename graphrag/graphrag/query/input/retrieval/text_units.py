# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Util functions to retrieve text units from a collection."""

from typing import Any, cast

import pandas as pd

from graphrag.data_model.entity import Entity
from graphrag.data_model.text_unit import TextUnit


def _get_documents_by_entity_neo4j(entity_name: str) -> list[dict[str, Any]]:
    """
    EXPERIMENTAL POC: Get documents mentioning an entity from Neo4j.
    
    This is an internal helper that attempts to use Neo4j for entity→document
    relationship lookup. Falls back to empty list if Neo4j is unavailable.
    
    Parameters
    ----------
    entity_name : str
        Name of the entity
        
    Returns
    -------
    list[dict]
        List of document dicts with keys: id, title, source
        Returns empty list if Neo4j is unavailable
    """
    try:
        from graphrag.graph.neo4j_client import get_documents_by_entity_neo4j as neo4j_func
        return neo4j_func(entity_name)
    except Exception:
        return []


def get_candidate_text_units(
    selected_entities: list[Entity],
    text_units: list[TextUnit],
) -> pd.DataFrame:
    """
    Get all text units that are associated to selected entities.
    
    EXPERIMENTAL POC: If Neo4j is enabled and at least one entity is provided,
    attempts to use Neo4j for entity→document relationship lookup for the first entity.
    Falls back to existing dataframe-based logic if Neo4j is unavailable.
    """
    # EXPERIMENTAL POC: Try Neo4j for entity→document lookup if enabled
    # Only use Neo4j for the first entity to keep the change minimal
    if selected_entities:
        first_entity = selected_entities[0]
        if first_entity.title:
            neo4j_docs = _get_documents_by_entity_neo4j(first_entity.title)
            if neo4j_docs:
                # Convert Neo4j documents to TextUnit-like objects
                # For POC simplicity, create minimal TextUnit objects from Neo4j results
                neo4j_text_units = []
                for doc in neo4j_docs:
                    # Create a TextUnit from Neo4j document data
                    # Use document title as text for simplicity in POC
                    text_unit = TextUnit(
                        id=doc.get("id", ""),
                        short_id=doc.get("id", ""),
                        text=doc.get("title", doc.get("source", "")),
                        document_ids=[doc.get("id", "")]
                    )
                    neo4j_text_units.append(text_unit)
                
                # Convert to dataframe
                if neo4j_text_units:
                    neo4j_df = to_text_unit_dataframe(neo4j_text_units)
                    # For remaining entities, use dataframe logic and merge results
                    if len(selected_entities) > 1:
                        remaining_entities = selected_entities[1:]
                        selected_text_ids = [
                            entity.text_unit_ids 
                            for entity in remaining_entities 
                            if entity.text_unit_ids
                        ]
                        selected_text_ids = [item for sublist in selected_text_ids for item in sublist]
                        selected_text_units = [
                            unit for unit in text_units 
                            if unit.id in selected_text_ids
                        ]
                        remaining_df = to_text_unit_dataframe(selected_text_units)
                        # Merge dataframes
                        return pd.concat([neo4j_df, remaining_df], ignore_index=True)
                    return neo4j_df
    
    # Fallback to existing dataframe-based logic
    selected_text_ids = [
        entity.text_unit_ids for entity in selected_entities if entity.text_unit_ids
    ]
    selected_text_ids = [item for sublist in selected_text_ids for item in sublist]
    selected_text_units = [unit for unit in text_units if unit.id in selected_text_ids]
    return to_text_unit_dataframe(selected_text_units)


def to_text_unit_dataframe(text_units: list[TextUnit]) -> pd.DataFrame:
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
    return pd.DataFrame(records, columns=cast("Any", header))
