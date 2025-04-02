# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Sort local context by total degree of associated nodes in descending order."""

import logging

import pandas as pd

import graphrag.data_model.schemas as schemas
from graphrag.query.llm.text_utils import num_tokens

log = logging.getLogger(__name__)


def get_context_string(
    text_units: list[dict],
    sub_community_reports: list[dict] | None = None,
) -> str:
    """Concatenate structured data into a context string."""
    contexts = []
    if sub_community_reports:
        sub_community_reports = [
            report
            for report in sub_community_reports
            if schemas.COMMUNITY_ID in report
            and report[schemas.COMMUNITY_ID]
            and str(report[schemas.COMMUNITY_ID]).strip() != ""
        ]
        report_df = pd.DataFrame(sub_community_reports).drop_duplicates()
        if not report_df.empty:
            if report_df[schemas.COMMUNITY_ID].dtype == float:
                report_df[schemas.COMMUNITY_ID] = report_df[
                    schemas.COMMUNITY_ID
                ].astype(int)
            report_string = (
                f"----REPORTS-----\n{report_df.to_csv(index=False, sep=',')}"
            )
            contexts.append(report_string)

    text_units = [
        unit
        for unit in text_units
        if "id" in unit and unit["id"] and str(unit["id"]).strip() != ""
    ]
    text_units_df = pd.DataFrame(text_units).drop_duplicates()
    if not text_units_df.empty:
        if text_units_df["id"].dtype == float:
            text_units_df["id"] = text_units_df["id"].astype(int)
        text_unit_string = (
            f"-----SOURCES-----\n{text_units_df.to_csv(index=False, sep=',')}"
        )
        contexts.append(text_unit_string)

    return "\n\n".join(contexts)


def sort_context(
    local_context: list[dict],
    sub_community_reports: list[dict] | None = None,
    max_context_tokens: int | None = None,
) -> str:
    """Sort local context (list of text units) by total degree of associated nodes in descending order."""
    sorted_text_units = sorted(
        local_context, key=lambda x: x[schemas.ENTITY_DEGREE], reverse=True
    )

    current_text_units = []
    context_string = ""
    for record in sorted_text_units:
        current_text_units.append(record)
        if max_context_tokens:
            new_context_string = get_context_string(
                current_text_units, sub_community_reports
            )
            if num_tokens(new_context_string) > max_context_tokens:
                break

            context_string = new_context_string

    if context_string == "":
        return get_context_string(sorted_text_units, sub_community_reports)

    return context_string
