# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

from uuid import uuid4

import pandas as pd


def finalize_community_reports(
    reports: pd.DataFrame,
    communities: pd.DataFrame,
) -> pd.DataFrame:
    """All the steps to transform final community reports."""
    # Merge with communities to add shared fields
    community_reports = reports.merge(
        communities.loc[:, ["community", "parent", "children", "size", "period"]],
        on="community",
        how="left",
        copy=False,
    )

    community_reports["community"] = community_reports["community"].astype(int)
    community_reports["human_readable_id"] = community_reports["community"]
    community_reports["id"] = [uuid4().hex for _ in range(len(community_reports))]

    return community_reports.loc[
        :,
        [
            "id",
            "human_readable_id",
            "community",
            "level",
            "parent",
            "children",
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
