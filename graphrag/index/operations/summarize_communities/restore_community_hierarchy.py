# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_graph, _get_node_attributes, _get_edge_attributes and _get_attribute_column_mapping methods definition."""

import logging
from itertools import pairwise

import pandas as pd

import graphrag.index.operations.summarize_communities.community_reports_extractor.schemas as schemas

log = logging.getLogger(__name__)


def restore_community_hierarchy(
    input: pd.DataFrame,
    name_column: str = schemas.NODE_NAME,
    community_column: str = schemas.NODE_COMMUNITY,
    level_column: str = schemas.NODE_LEVEL,
) -> pd.DataFrame:
    """Restore the community hierarchy from the node data."""
    # Group by community and level, aggregate names as lists
    community_df = (
        input.groupby([community_column, level_column])[name_column]
        .apply(set)
        .reset_index()
    )

    # Build dictionary with levels as integers
    community_levels = {
        level: group.set_index(community_column)[name_column].to_dict()
        for level, group in community_df.groupby(level_column)
    }

    # get unique levels, sorted in ascending order
    levels = sorted(community_levels.keys())  # type: ignore
    community_hierarchy = []

    # Iterate through adjacent levels
    for current_level, next_level in pairwise(levels):
        current_communities = community_levels[current_level]
        next_communities = community_levels[next_level]

        # Find sub-communities
        for curr_comm, curr_entities in current_communities.items():
            for next_comm, next_entities in next_communities.items():
                if next_entities.issubset(curr_entities):
                    community_hierarchy.append({
                        community_column: curr_comm,
                        schemas.COMMUNITY_LEVEL: current_level,
                        schemas.SUB_COMMUNITY: next_comm,
                        schemas.SUB_COMMUNITY_SIZE: len(next_entities),
                    })

    return pd.DataFrame(
        community_hierarchy,
    )
