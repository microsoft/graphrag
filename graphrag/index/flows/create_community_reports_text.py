# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform community reports."""

import logging

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config import defaults
from graphrag.config.enums import AsyncType
from graphrag.index.operations.finalize_community_reports import (
    finalize_community_reports,
)
from graphrag.index.operations.summarize_communities import (
    summarize_communities,
)
from graphrag.index.operations.summarize_communities.prep_level_contexts import (
    prep_level_contexts,
)
from graphrag.index.operations.summarize_communities_text.context_builder import (
    prep_local_context,
)
from graphrag.index.operations.summarize_communities_text.prompts import (
    COMMUNITY_REPORT_PROMPT,
)

log = logging.getLogger(__name__)


async def create_community_reports_text(
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
    community_join = communities.explode("entity_ids").loc[
        :, ["community", "level", "entity_ids"]
    ]
    nodes = entities.merge(
        community_join, left_on="id", right_on="entity_ids", how="left"
    )
    nodes = nodes.loc[nodes.loc[:, "community"] != -1]

    max_input_length = summarization_strategy.get(
        "max_input_length", defaults.COMMUNITY_REPORT_MAX_INPUT_LENGTH
    )

    # TEMP: forcing override of the prompt until we can put it into config
    summarization_strategy["extraction_prompt"] = COMMUNITY_REPORT_PROMPT
    # build initial local context for all communities
    local_contexts = prep_local_context(
        communities, text_units, nodes, max_input_length
    )

    level_contexts = prep_level_contexts(
        nodes,
        local_contexts,
        max_input_length,
    )

    community_reports = await summarize_communities(
        local_contexts,
        level_contexts,
        callbacks,
        cache,
        summarization_strategy,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    return finalize_community_reports(community_reports, communities)
