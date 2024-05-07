# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Community Context."""

import random
from typing import Any, cast

import pandas as pd
import tiktoken

from graphrag.model import CommunityReport, Entity
from graphrag.query.llm.text_utils import num_tokens


def build_community_context(
    community_reports: list[CommunityReport],
    entities: list[Entity] | None = None,
    token_encoder: tiktoken.Encoding | None = None,
    use_community_summary: bool = True,
    column_delimiter: str = "|",
    shuffle_data: bool = True,
    include_community_rank: bool = False,
    min_community_rank: int = 0,
    community_rank_name: str = "rank",
    community_weight_name: str = "weight",
    max_tokens: int = 8000,
    single_batch: bool = True,
    context_name: str = "Reports",
    random_state: int = 86,
) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
    """
    Prepare community report data table as context data for system prompt.
    If entities are provided, the community weight is calculated as the count of text units associated with entities within the community.
    The calculated weight is added as an attribute to the community reports and added to the context data table.
    """
    if entities and len(community_reports) > 0 and community_weight_name not in community_reports[0].attributes:
        community_reports = _compute_community_weights(community_reports, entities)

    selected_reports = [
        report
        for report in community_reports
        if report.rank and report.rank >= min_community_rank
    ]
    if selected_reports is None or len(selected_reports) == 0:
        return ([], {})

    if shuffle_data:
        random.seed(random_state)
        random.shuffle(selected_reports)

    # add context header
    current_context_text = f"-----{context_name}-----" + "\n"

    # add header
    header = ["id", "title"]
    attribute_cols = (
        list(selected_reports[0].attributes.keys())
        if selected_reports[0].attributes
        else []
    )
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)
    header.append("summary" if use_community_summary else "content")
    if include_community_rank:
        header.append(community_rank_name)
    
    current_context_text += column_delimiter.join(header) + "\n"
    current_tokens = num_tokens(current_context_text, token_encoder)
    results = []
    all_context_records = [header]

    for report in selected_reports:
        new_context = [
            report.short_id,
            report.title,
            *[
                str(report.attributes.get(field, "")) if report.attributes else ""
                for field in attribute_cols
            ],
        ]
        new_context.append(
            report.summary if use_community_summary else report.full_content
        )
        if include_community_rank:
            new_context.append(str(report.rank))
        new_context_text = column_delimiter.join(new_context) + "\n"
        all_context_records.append(new_context)

        new_tokens = num_tokens(new_context_text, token_encoder)
        if current_tokens + new_tokens > max_tokens:
            if single_batch:
                # convert all_context_records to pandas dataframe
                if len(all_context_records) > 1:
                    record_df = pd.DataFrame(
                        all_context_records[1:-1],
                        columns=cast(Any, all_context_records[0]),
                    )
                    record_df = _rank_report_context(
                        report_df=record_df,
                        weight_column=community_weight_name if entities else None,
                        rank_column=community_rank_name if include_community_rank else None,
                    )
                else:
                    record_df = pd.DataFrame()
                return current_context_text, {context_name.lower(): record_df}

            results.append(current_context_text)

            # start a new batch
            current_context_text = (
                f"-----{context_name}-----"
                + "\n"
                + column_delimiter.join(header)
                + "\n"
            )
            current_tokens = num_tokens(current_context_text, token_encoder)
        else:
            current_context_text += new_context_text
            current_tokens += new_tokens
    if current_context_text not in results:
        results.append(current_context_text)
    if len(all_context_records) > 1:
        record_df = pd.DataFrame(
            all_context_records[1:], columns=cast(Any, all_context_records[0])
        )
        record_df = _rank_report_context(
            report_df=record_df,
            weight_column=community_weight_name if entities else None,
            rank_column=community_rank_name if include_community_rank else None,
        )
    else:
        record_df = pd.DataFrame()
    return results, {context_name.lower(): record_df}

def _compute_community_weights(
        community_reports: list[CommunityReport],
        entities: list[Entity],
        weight_attribute: str = "weight"     
) -> list[CommunityReport]:
    """Calculate a community's weight as count of text units associated with entities within the community"""
    community_text_units = {}
    for entity in entities:
        for community_id in entity.community_ids:
            if community_id not in community_text_units:
                community_text_units[community_id] = []
            community_text_units[community_id].extend(entity.text_unit_ids)
    for report in community_reports:
        report.attributes[weight_attribute] = len(set(community_text_units.get(report.community_id, [])))
    return community_reports

def _rank_report_context(
        report_df: pd.DataFrame,
        weight_column: str | None = "weight",
        rank_column: str | None = "rank",
) -> pd.DataFrame:
    """Rank and sort report context by community weight and rank if exist."""
    rank_attributes = []
    if weight_column:
        rank_attributes.append(weight_column)
    if rank_column:
        rank_attributes.append(rank_column)
    if len(rank_attributes) > 0:
        report_df.sort_values(by=rank_attributes, ascending=False, inplace=True)
    return report_df