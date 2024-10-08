# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform community reports."""

from typing import cast

import pandas as pd
from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.cache import PipelineCache
from graphrag.index.flows.create_final_community_reports import (
    create_final_community_reports as create_final_community_reports_flow,
)
from graphrag.index.utils.ds_util import get_named_input_table, get_required_input_table


@verb(name="create_final_community_reports", treats_input_tables_as_immutable=True)
async def create_final_community_reports(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    summarization_strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
    full_content_text_embed: dict | None = None,
    summary_text_embed: dict | None = None,
    title_text_embed: dict | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform community reports."""
    nodes = cast(pd.DataFrame, input.get_input())
    edges = cast(pd.DataFrame, get_required_input_table(input, "relationships").table)

    claims = get_named_input_table(input, "covariates")
    if claims:
        claims = cast(pd.DataFrame, claims.table)

    output = await create_final_community_reports_flow(
        nodes,
        edges,
        claims,
        callbacks,
        cache,
        summarization_strategy,
        async_mode=async_mode,
        num_threads=num_threads,
        full_content_text_embed=full_content_text_embed,
        summary_text_embed=summary_text_embed,
        title_text_embed=title_text_embed,
    )

    return create_verb_result(
        cast(
            Table,
            output,
        )
    )
