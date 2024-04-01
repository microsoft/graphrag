#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Community Context."""
import random
from typing import Any, cast

import pandas as pd
import tiktoken

from graphrag.model import CommunityReport
from graphrag.query.llm.text_utils import num_tokens


def build_community_context(
    community_reports: list[CommunityReport],
    token_encoder: tiktoken.Encoding | None = None,
    use_community_summary: bool = True,
    column_delimiter: str = "|",
    shuffle_data: bool = True,
    include_community_rank: bool = False,
    min_community_rank: int = 0,
    max_tokens: int = 8000,
    single_batch: bool = True,
    context_name: str = "Reports",
    random_state: int = 86,
) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
    """Prepare community report data table as context data for system prompt."""
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
        header.append("rank")

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
    else:
        record_df = pd.DataFrame()
    return results, {context_name.lower(): record_df}
