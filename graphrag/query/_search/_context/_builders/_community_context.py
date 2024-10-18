# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Module for building community context data for system prompts in the GraphRAG framework.

Functions:
    build_community_context: Prepares community report data as context for system prompts.
    _compute_community_weights: Calculates community weight based on associated entities and text units.
    _rank_report_context: Sorts community report data by community weight and rank.
    _convert_report_context_to_df: Converts community report context records into a pandas DataFrame.
"""

from __future__ import annotations

import random
import typing

import pandas as pd
import tiktoken

from .. import _types
from ... import _model
from .... import _utils


def build_community_context(
    community_reports: typing.List[_model.CommunityReport],
    entities: typing.Optional[typing.List[_model.Entity]] = None,
    token_encoder: typing.Optional[tiktoken.Encoding] = None,
    use_community_summary: bool = True,
    column_delimiter: str = "|",
    shuffle_data: bool = True,
    include_community_rank: bool = False,
    min_community_rank: int = 0,
    community_rank_name: str = "rank",
    include_community_weight: bool = True,
    community_weight_name: str = "occurrence weight",
    normalize_community_weight: bool = True,
    data_max_tokens: int = 8000,
    single_batch: bool = True,
    context_name: str = "Reports",
    random_state: int = 86,
) -> _types.Context_T:
    """
    Prepares community report data as a context table for system prompts.

    Args:
        community_reports:
            A list of community reports to include in the context.
        entities:
            An optional list of entities associated with the community reports.
        token_encoder: An optional token encoder for calculating token counts.
        use_community_summary:
            Whether to use the community summary or the full content.
        column_delimiter:
            The delimiter to use for separating columns in the context data.
        shuffle_data:
            Whether to shuffle the community reports before adding them to the
            context.
        include_community_rank:
            Whether to include community rank in the context.
        min_community_rank:
            The minimum rank required for a community report to be included.
        community_rank_name: The name of the column used for community rank.
        include_community_weight:
            Whether to include community weight in the context.
        community_weight_name: The name of the column used for community weight.
        normalize_community_weight:
            Whether to normalize the community weight across reports.
        data_max_tokens:
            The maximum number of tokens allowed in the context data.
        single_batch: Whether to limit the context to a single batch.
        context_name: The name to use for the context section.
        random_state:
            A seed used to shuffle the community reports (if shuffle_data is
            True).

    Returns:
        A tuple containing the formatted context string and a dictionary with
        the context data as a DataFrame.
    """

    def _is_included(report: _model.CommunityReport) -> bool:
        return report.rank is not None and report.rank >= min_community_rank

    def _get_header(attr: typing.List[str]) -> typing.List[str]:
        _header = ["id", "title"]
        attr = [col for col in attr if col not in _header]
        if not include_community_weight:
            attr = [col for col in attr if col != community_weight_name]
        _header.extend(attr)
        _header.append("summary" if use_community_summary else "content")
        if include_community_rank:
            _header.append(community_rank_name)
        return _header

    def _report_context_text(
        report: _model.CommunityReport, attr: typing.List[str]
    ) -> typing.Tuple[str, typing.List[str]]:
        ctx = [report.short_id if report.short_id else "", report.title, *[
            str(report.attributes.get(field, "")) if report.attributes else ""
            for field in attr
        ], report.summary if use_community_summary else report.full_content]
        if include_community_rank:
            ctx.append(str(report.rank))
        result = column_delimiter.join(ctx) + "\n"
        return result, ctx

    compute_community_weights = (
            entities
            and len(community_reports) > 0
            and include_community_weight
            and (
                    community_reports[0].attributes is None
                    or community_weight_name not in community_reports[0].attributes
            )
    )
    if compute_community_weights:
        community_reports = _compute_community_weights(
            community_reports=community_reports,
            entities=entities,
            weight_attribute=community_weight_name,
            normalize=normalize_community_weight,
        )

    selected_reports = [report for report in community_reports if _is_included(report)]

    if selected_reports is None or len(selected_reports) == 0:
        return [], {}

    if shuffle_data:
        random.seed(random_state)
        random.shuffle(selected_reports)

    # "global" variables
    attributes = (
        list(community_reports[0].attributes.keys())
        if community_reports[0].attributes
        else []
    )
    header = _get_header(attributes)
    all_context_text: typing.List[str] = []
    all_context_records: typing.List[pd.DataFrame] = []

    # batch variables
    batch_text: str = ""
    batch_tokens: int = 0
    batch_records: typing.List[typing.List[str]] = []

    def _init_batch() -> None:
        nonlocal batch_text, batch_tokens, batch_records
        batch_text = (
                f"-----{context_name}-----" + "\n" + column_delimiter.join(header) + "\n"
        )
        batch_tokens = _utils.num_tokens(batch_text, token_encoder)
        batch_records = []

    def _cut_batch() -> None:
        # convert the current context records to pandas dataframe and sort by weight and rank if exist
        record_df = _convert_report_context_to_df(
            context_records=batch_records,
            header=header,
            weight_column=(
                community_weight_name if entities and include_community_weight else None
            ),
            rank_column=community_rank_name if include_community_rank else None,
        )
        if len(record_df) == 0:
            return
        current_context_text = record_df.to_csv(index=False, sep=column_delimiter)
        all_context_text.append(current_context_text)
        all_context_records.append(record_df)

    # initialize the first batch
    _init_batch()

    for report in selected_reports:
        new_context_text, new_context = _report_context_text(report, attributes)
        new_tokens = _utils.num_tokens(new_context_text, token_encoder)

        if batch_tokens + new_tokens > data_max_tokens:
            # add the current batch to the context data and start a new batch if we are in multi-batch mode
            _cut_batch()
            if single_batch:
                break
            _init_batch()

        # add current report to the current batch
        batch_text += new_context_text
        batch_tokens += new_tokens
        batch_records.append(new_context)

    # add the last batch if it has not been added
    if batch_text not in all_context_text:
        _cut_batch()

    if len(all_context_records) == 0:
        return [], {}

    return all_context_text, {
        context_name.lower(): pd.concat(all_context_records, ignore_index=True)
    }


def _compute_community_weights(
    community_reports: typing.List[_model.CommunityReport],
    entities: typing.Optional[typing.List[_model.Entity]],
    weight_attribute: str = "occurrence",
    normalize: bool = True,
) -> typing.List[_model.CommunityReport]:
    """
    Calculates a community's weight as the count of text units associated with
    entities in the community.

    Args:
        community_reports:
            A list of community reports to update with weight information.
        entities:
            A list of entities to use for calculating the community weights.
        weight_attribute:
            The name of the attribute to store the calculated weight.
        normalize:
            Whether to normalize the weights across all community reports.

    Returns:
        A list of community reports with updated weight information.
    """
    if not entities:
        return community_reports

    community_text_units: typing.Dict[str, typing.List[str]] = {}
    for entity in entities:
        if entity.community_ids:
            for community_id in entity.community_ids:
                if community_id not in community_text_units:
                    community_text_units[community_id] = []
                community_text_units[community_id].extend(entity.text_unit_ids or [])
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
    weight_column: typing.Optional[str] = "occurrence weight",
    rank_column: typing.Optional[str] = "rank",
) -> pd.DataFrame:
    """
    Sorts the report context by community weight and rank, if these attributes
    are provided.

    Args:
        report_df: A DataFrame containing the community report data.
        weight_column: The name of the column containing community weights.
        rank_column: The name of the column containing community ranks.

    Returns:
        A sorted DataFrame based on the community weight and rank.
    """
    rank_attributes: typing.List[str] = []
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
    context_records: typing.List[typing.List[str]],
    header: typing.List[str],
    weight_column: typing.Optional[str] = None,
    rank_column: typing.Optional[str] = None,
) -> pd.DataFrame:
    """
    Converts community report context records into a pandas DataFrame and sorts
    by weight and rank.

    Args:
        context_records: A list of records representing community reports.
        header: A list of column headers for the DataFrame.
        weight_column: An optional column name for community weights.
        rank_column: An optional column name for community ranks.

    Returns:
        A pandas DataFrame containing the community report context data.
    """
    if len(context_records) == 0:
        return pd.DataFrame()

    record_df = pd.DataFrame(
        context_records,
        columns=typing.cast(typing.Any, header),
    )
    return _rank_report_context(
        report_df=record_df,
        weight_column=weight_column,
        rank_column=rank_column,
    )
