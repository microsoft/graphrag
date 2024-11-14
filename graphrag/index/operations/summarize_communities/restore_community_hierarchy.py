# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_graph, _get_node_attributes, _get_edge_attributes and _get_attribute_column_mapping methods definition."""

import logging

import pandas as pd

import graphrag.index.graph.extractors.community_reports.schemas as schemas

log = logging.getLogger(__name__)


def restore_community_hierarchy(
    input: pd.DataFrame,
    name_column: str = schemas.NODE_NAME,
    community_column: str = schemas.NODE_COMMUNITY,
    level_column: str = schemas.NODE_LEVEL,
) -> pd.DataFrame:
    """Restore the community hierarchy from the node data."""
    community_df = (
        input.groupby([community_column, level_column])
        .agg({name_column: list})
        .reset_index()
    )
    community_levels = {}
    for _, row in community_df.iterrows():
        level = row[level_column]
        name = row[name_column]
        community = row[community_column]

        if community_levels.get(level) is None:
            community_levels[level] = {}
        community_levels[level][community] = name

    # get unique levels, sorted in ascending order
    levels = sorted(community_levels.keys())
    community_hierarchy = []

    for idx in range(len(levels) - 1):
        level = levels[idx]
        next_level = levels[idx + 1]
        current_level_communities = community_levels[level]
        next_level_communities = community_levels[next_level]

        for current_community in current_level_communities:
            current_entities = current_level_communities[current_community]

            # loop through next level's communities to find all the subcommunities
            entities_found = 0
            for next_level_community in next_level_communities:
                next_entities = next_level_communities[next_level_community]
                if set(next_entities).issubset(set(current_entities)):
                    community_hierarchy.append({
                        community_column: current_community,
                        schemas.COMMUNITY_LEVEL: level,
                        schemas.SUB_COMMUNITY: next_level_community,
                        schemas.SUB_COMMUNITY_SIZE: len(next_entities),
                    })

                    entities_found += len(next_entities)
                    if entities_found == len(current_entities):
                        break

    return pd.DataFrame(
        community_hierarchy,
    )
