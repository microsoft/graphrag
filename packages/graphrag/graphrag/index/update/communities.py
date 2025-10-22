# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Dataframe operations and utils for Incremental Indexing."""

import pandas as pd

from graphrag.data_model.schemas import (
    COMMUNITIES_FINAL_COLUMNS,
    COMMUNITY_REPORTS_FINAL_COLUMNS,
)


def _update_and_merge_communities(
    old_communities: pd.DataFrame,
    delta_communities: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """Update and merge communities.

    Parameters
    ----------
    old_communities : pd.DataFrame
        The old communities.
    delta_communities : pd.DataFrame
        The delta communities.
    community_id_mapping : dict
        The community id mapping.

    Returns
    -------
    pd.DataFrame
        The updated communities.
    """
    # Check if size and period columns exist in the old_communities. If not, add them
    if "size" not in old_communities.columns:
        old_communities["size"] = None
    if "period" not in old_communities.columns:
        old_communities["period"] = None

    # Same for delta_communities
    if "size" not in delta_communities.columns:
        delta_communities["size"] = None
    if "period" not in delta_communities.columns:
        delta_communities["period"] = None

    # Increment all community ids by the max of the old communities
    old_max_community_id = old_communities["community"].fillna(0).astype(int).max()
    # Increment only the non-NaN values in delta_communities["community"]
    community_id_mapping = {
        v: v + old_max_community_id + 1
        for k, v in delta_communities["community"].dropna().astype(int).items()
    }
    community_id_mapping.update({-1: -1})

    # Look for community ids in community and replace them with the corresponding id in the mapping
    delta_communities["community"] = (
        delta_communities["community"]
        .astype(int)
        .apply(lambda x: community_id_mapping.get(x, x))
    )

    delta_communities["parent"] = (
        delta_communities["parent"]
        .astype(int)
        .apply(lambda x: community_id_mapping.get(x, x))
    )

    old_communities["community"] = old_communities["community"].astype(int)

    # Merge the final communities
    merged_communities = pd.concat(
        [old_communities, delta_communities], ignore_index=True, copy=False
    )

    # Rename title
    merged_communities["title"] = "Community " + merged_communities["community"].astype(
        str
    )
    # Re-assign the human_readable_id
    merged_communities["human_readable_id"] = merged_communities["community"]

    merged_communities = merged_communities.loc[
        :,
        COMMUNITIES_FINAL_COLUMNS,
    ]
    return merged_communities, community_id_mapping


def _update_and_merge_community_reports(
    old_community_reports: pd.DataFrame,
    delta_community_reports: pd.DataFrame,
    community_id_mapping: dict,
) -> pd.DataFrame:
    """Update and merge community reports.

    Parameters
    ----------
    old_community_reports : pd.DataFrame
        The old community reports.
    delta_community_reports : pd.DataFrame
        The delta community reports.
    community_id_mapping : dict
        The community id mapping.

    Returns
    -------
    pd.DataFrame
        The updated community reports.
    """
    # Check if size and period columns exist in the old_community_reports. If not, add them
    if "size" not in old_community_reports.columns:
        old_community_reports["size"] = None
    if "period" not in old_community_reports.columns:
        old_community_reports["period"] = None

    # Same for delta_community_reports
    if "size" not in delta_community_reports.columns:
        delta_community_reports["size"] = None
    if "period" not in delta_community_reports.columns:
        delta_community_reports["period"] = None

    # Look for community ids in community and replace them with the corresponding id in the mapping
    delta_community_reports["community"] = (
        delta_community_reports["community"]
        .astype(int)
        .apply(lambda x: community_id_mapping.get(x, x))
    )

    delta_community_reports["parent"] = (
        delta_community_reports["parent"]
        .astype(int)
        .apply(lambda x: community_id_mapping.get(x, x))
    )

    old_community_reports["community"] = old_community_reports["community"].astype(int)

    # Merge the final community reports
    merged_community_reports = pd.concat(
        [old_community_reports, delta_community_reports], ignore_index=True, copy=False
    )

    # Maintain type compat with query
    merged_community_reports["community"] = merged_community_reports[
        "community"
    ].astype(int)
    # Re-assign the human_readable_id
    merged_community_reports["human_readable_id"] = merged_community_reports[
        "community"
    ]

    return merged_community_reports.loc[:, COMMUNITY_REPORTS_FINAL_COLUMNS]
