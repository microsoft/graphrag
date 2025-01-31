# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing community report generation utilities."""

from itertools import pairwise

import pandas as pd

import graphrag.model.schemas as schemas


def get_levels(
    df: pd.DataFrame, level_column: str = schemas.COMMUNITY_LEVEL
) -> list[int]:
    """Get the levels of the communities."""
    levels = df[level_column].dropna().unique()
    levels = [int(lvl) for lvl in levels if lvl != -1]
    return sorted(levels, reverse=True)


def restore_community_hierarchy(
    input: pd.DataFrame,
    name_column: str = schemas.TITLE,
    community_column: str = schemas.COMMUNITY_ID,
    level_column: str = schemas.COMMUNITY_LEVEL,
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
