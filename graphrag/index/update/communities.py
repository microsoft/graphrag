# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Dataframe operations and utils for Incremental Indexing."""

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Callable


def _merge_and_resolve_nodes(
    old_nodes: pd.DataFrame, delta_nodes: pd.DataFrame, merged_entities_df: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """Merge and resolve nodes.

    Parameters
    ----------
    old_nodes : pd.DataFrame
        The old nodes.
    delta_nodes : pd.DataFrame
        The delta nodes.

    Returns
    -------
    pd.DataFrame
        The merged nodes.
    dict
        The community id mapping.
    """
    # Increment all community ids by the max of the old nodes
    old_max_community_id = old_nodes["community"].fillna(0).astype(int).max()

    # Merge delta_nodes with merged_entities_df to get the new human_readable_id
    delta_nodes = delta_nodes.merge(
        merged_entities_df[["id", "human_readable_id"]],
        on="id",
        how="left",
        suffixes=("", "_new"),
    )

    # Replace existing human_readable_id with the new one from merged_entities_df
    delta_nodes["human_readable_id"] = delta_nodes.loc[
        :, "human_readable_id_new"
    ].combine_first(delta_nodes.loc[:, "human_readable_id"])

    # Drop the auxiliary column from the merge
    delta_nodes.drop(columns=["human_readable_id_new"], inplace=True)

    # Increment only the non-NaN values in delta_nodes["community"]
    community_id_mapping = {
        v: v + old_max_community_id + 1
        for k, v in delta_nodes["community"].dropna().astype(int).items()
    }

    delta_nodes["community"] = delta_nodes["community"].where(
        delta_nodes["community"].isna(),
        delta_nodes["community"].fillna(0).astype(int) + old_max_community_id + 1,
    )

    # Concat the DataFrames
    concat_nodes = pd.concat([old_nodes, delta_nodes], ignore_index=True)
    columns_to_agg: dict[str, str | Callable] = {
        col: "first" for col in concat_nodes.columns if col not in ["level", "title"]
    }

    merged_nodes = (
        concat_nodes.groupby(["level", "title"]).agg(columns_to_agg).reset_index()
    )

    merged_nodes["community"] = merged_nodes["community"].astype(int)
    merged_nodes["human_readable_id"] = merged_nodes["human_readable_id"].astype(int)

    merged_nodes = merged_nodes.loc[
        :,
        [
            "id",
            "human_readable_id",
            "title",
            "community",
            "level",
            "degree",
            "x",
            "y",
        ],
    ]

    return merged_nodes, community_id_mapping


def _update_and_merge_communities(
    old_communities: pd.DataFrame,
    delta_communities: pd.DataFrame,
    community_id_mapping: dict,
) -> pd.DataFrame:
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

    # Look for community ids in community and replace them with the corresponding id in the mapping
    delta_communities["community"] = (
        delta_communities["community"]
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

    return merged_communities.loc[
        :,
        [
            "id",
            "human_readable_id",
            "community",
            "level",
            "title",
            "entity_ids",
            "relationship_ids",
            "text_unit_ids",
            "period",
            "size",
        ],
    ]


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

    return merged_community_reports.loc[
        :,
        [
            "id",
            "human_readable_id",
            "community",
            "level",
            "title",
            "summary",
            "full_content",
            "rank",
            "rank_explanation",
            "findings",
            "full_content_json",
            "period",
            "size",
        ],
    ]
