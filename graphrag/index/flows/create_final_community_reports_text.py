# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform community reports."""

import logging
from uuid import uuid4

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config import defaults
from graphrag.config.enums import AsyncType
from graphrag.index.operations.summarize_communities import (
    summarize_communities,
)
from graphrag.index.operations.summarize_communities_text.context_builder import (
    prep_community_report_context,
    prep_local_context,
)
from graphrag.index.operations.summarize_communities_text.prompts import (
    COMMUNITY_REPORT_PROMPT,
)

log = logging.getLogger(__name__)


async def create_final_community_reports_text(
    nodes_input: pd.DataFrame,
    entities: pd.DataFrame,
    communities: pd.DataFrame,
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    summarization_strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
) -> pd.DataFrame:
    """All the steps to transform community reports."""
    entities_df = entities.loc[:, ["id", "text_unit_ids"]]
    nodes_df = nodes_input.merge(entities_df, on="id")
    nodes = nodes_df.loc[nodes_df.loc[:, "community"] != -1]

    # TEMP: forcing override of the prompt until we can put it into config
    summarization_strategy["extraction_prompt"] = COMMUNITY_REPORT_PROMPT

    max_input_length = summarization_strategy.get(
        "max_input_length", defaults.COMMUNITY_REPORT_MAX_INPUT_LENGTH
    )

    local_contexts = prep_local_context(
        communities, text_units, nodes, max_input_length
    )

    community_reports = await summarize_communities(
        nodes,
        local_contexts,
        prep_community_report_context,
        callbacks,
        cache,
        summarization_strategy,
        max_input_length=max_input_length,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    community_reports["community"] = community_reports["community"].astype(int)
    community_reports["human_readable_id"] = community_reports["community"]
    community_reports["id"] = [uuid4().hex for _ in range(len(community_reports))]

    # Merge with communities to add size and period
    merged = community_reports.merge(
        communities.loc[:, ["community", "parent", "size", "period"]],
        on="community",
        how="left",
        copy=False,
    )
    return merged.loc[
        :,
        [
            "id",
            "human_readable_id",
            "community",
            "parent",
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
