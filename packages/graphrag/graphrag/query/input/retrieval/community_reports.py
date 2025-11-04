# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Util functions to retrieve community reports from a collection."""

from typing import Any, cast

import pandas as pd

from graphrag.data_model.community_report import CommunityReport
from graphrag.data_model.entity import Entity


def get_candidate_communities(
    selected_entities: list[Entity],
    community_reports: list[CommunityReport],
    include_community_rank: bool = False,
    use_community_summary: bool = False,
) -> pd.DataFrame:
    """Get all communities that are related to selected entities."""
    selected_community_ids = [
        entity.community_ids for entity in selected_entities if entity.community_ids
    ]
    selected_community_ids = [
        item for sublist in selected_community_ids for item in sublist
    ]
    selected_reports = [
        community
        for community in community_reports
        if community.id in selected_community_ids
    ]
    return to_community_report_dataframe(
        reports=selected_reports,
        include_community_rank=include_community_rank,
        use_community_summary=use_community_summary,
    )


def to_community_report_dataframe(
    reports: list[CommunityReport],
    include_community_rank: bool = False,
    use_community_summary: bool = False,
) -> pd.DataFrame:
    """Convert a list of communities to a pandas dataframe."""
    if len(reports) == 0:
        return pd.DataFrame()

    # add header
    header = ["id", "title"]
    attribute_cols = list(reports[0].attributes.keys()) if reports[0].attributes else []
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)
    header.append("summary" if use_community_summary else "content")
    if include_community_rank:
        header.append("rank")

    records = []
    for report in reports:
        new_record = [
            report.short_id if report.short_id else "",
            report.title,
            *[
                str(report.attributes.get(field, ""))
                if report.attributes and report.attributes.get(field)
                else ""
                for field in attribute_cols
            ],
        ]
        new_record.append(
            report.summary if use_community_summary else report.full_content
        )
        if include_community_rank:
            new_record.append(str(report.rank))
        records.append(new_record)
    return pd.DataFrame(records, columns=cast("Any", header))
