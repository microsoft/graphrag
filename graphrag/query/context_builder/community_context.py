# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Community Context."""

import logging
import random
from typing import Any, cast

import pandas as pd
import tiktoken

from graphrag.model import CommunityReport, Entity
from graphrag.query.llm.text_utils import num_tokens

log = logging.getLogger(__name__)


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
    include_community_weight: bool = True,
    community_weight_name: str = "occurrence weight",
    normalize_community_weight: bool = True,
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
    if (
        entities
        and len(community_reports) > 0
        and include_community_weight
        and (
            community_reports[0].attributes is None
            or community_weight_name not in community_reports[0].attributes
        )
    ):
        log.info("Computing community weights...")
        community_reports = _compute_community_weights(
            community_reports=community_reports,
            entities=entities,
            weight_attribute=community_weight_name,
            normalize=normalize_community_weight,
        )

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
    if not include_community_weight:
        attribute_cols = [col for col in attribute_cols if col != community_weight_name]
    header.extend(attribute_cols)
    header.append("summary" if use_community_summary else "content")
    if include_community_rank:
        header.append(community_rank_name)

    current_context_text += column_delimiter.join(header) + "\n"
    current_tokens = num_tokens(current_context_text, token_encoder)
    current_context_records = [header]
    all_context_text = []
    all_context_records = []

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

        new_tokens = num_tokens(new_context_text, token_encoder)
        if current_tokens + new_tokens > max_tokens:
            # convert the current context records to pandas dataframe and sort by weight and rank if exist
            if len(current_context_records) > 1:
                record_df = _convert_report_context_to_df(
                    context_records=current_context_records[1:],
                    header=current_context_records[0],
                    weight_column=community_weight_name
                    if entities and include_community_weight
                    else None,
                    rank_column=community_rank_name if include_community_rank else None,
                )

            else:
                record_df = pd.DataFrame()
            current_context_text = record_df.to_csv(index=False, sep=column_delimiter)

            if single_batch:
                return current_context_text, {context_name.lower(): record_df}

            all_context_text.append(current_context_text)
            all_context_records.append(record_df)

            # start a new batch
            current_context_text = (
                f"-----{context_name}-----"
                + "\n"
                + column_delimiter.join(header)
                + "\n"
            )
            current_tokens = num_tokens(current_context_text, token_encoder)
            current_context_records = [header]
        else:
            current_context_text += new_context_text
            current_tokens += new_tokens
            current_context_records.append(new_context)

    # add the last batch if it has not been added
    if current_context_text not in all_context_text:
        if len(current_context_records) > 1:
            record_df = _convert_report_context_to_df(
                context_records=current_context_records[1:],
                header=current_context_records[0],
                weight_column=community_weight_name
                if entities and include_community_weight
                else None,
                rank_column=community_rank_name if include_community_rank else None,
            )
        else:
            record_df = pd.DataFrame()
        all_context_records.append(record_df)
        current_context_text = record_df.to_csv(index=False, sep=column_delimiter)
        all_context_text.append(current_context_text)

    return all_context_text, {
        context_name.lower(): pd.concat(all_context_records, ignore_index=True)
    }


def _compute_community_weights(
    community_reports: list[CommunityReport],
    entities: list[Entity],
    weight_attribute: str = "occurrence",
    normalize: bool = True,
) -> list[CommunityReport]:
    """Calculate a community's weight as count of text units associated with entities within the community."""
    community_text_units = {}
    for entity in entities:
        if entity.community_ids:
            for community_id in entity.community_ids:
                if community_id not in community_text_units:
                    community_text_units[community_id] = []
                community_text_units[community_id].extend(entity.text_unit_ids)
    for report in community_reports:
        if not report.attributes:
            report.attributes = {}
        report.attributes[weight_attribute] = len(
            set(community_text_units.get(report.community_id, []))
        )
    if normalize:
        # normalize by max weight
        all_weights = [
            report.attributes[weight_attribute]
            for report in community_reports
            if report.attributes
        ]
        max_weight = max(all_weights)
        for report in community_reports:
            if report.attributes:
                report.attributes[weight_attribute] = (
                    report.attributes[weight_attribute] / max_weight
                )
    return community_reports


def _rank_report_context(
    report_df: pd.DataFrame,
    weight_column: str | None = "occurrence weight",
    rank_column: str | None = "rank",
) -> pd.DataFrame:
    """Sort report context by community weight and rank if exist."""
    rank_attributes = []
    if weight_column:
        rank_attributes.append(weight_column)
        report_df[weight_column] = report_df[weight_column].astype(float)
    if rank_column:
        rank_attributes.append(rank_column)
        report_df[rank_column] = report_df[rank_column].astype(float)
    if len(rank_attributes) > 0:
        report_df.sort_values(by=rank_attributes, ascending=False, inplace=True)
    return report_df


def _convert_report_context_to_df(
    context_records: list[list[str]],
    header: list[str],
    weight_column: str | None = None,
    rank_column: str | None = None,
) -> pd.DataFrame:
    """Convert report context records to pandas dataframe and sort by weight and rank if exist."""
    record_df = pd.DataFrame(
        context_records,
        columns=cast(Any, header),
    )
    return _rank_report_context(
        report_df=record_df,
        weight_column=weight_column,
        rank_column=rank_column,
    )
