# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform community reports."""

from typing import cast
from uuid import uuid4

import pandas as pd
from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result
from graphrag.index.utils.ds_util import get_required_input_table
from graphrag.index.graph.extractors.community_reports.schemas import (
    NODE_DEGREE,
    NODE_DESCRIPTION,
    NODE_DETAILS,
    NODE_ID,
    NODE_NAME,
)
from graphrag.index.graph.extractors.community_reports.schemas import (
    EDGE_DEGREE,
    EDGE_DESCRIPTION,
    EDGE_DETAILS,
    EDGE_ID,
    EDGE_SOURCE,
    EDGE_TARGET,
)
from graphrag.index.graph.extractors.community_reports.schemas import (
    CLAIM_DESCRIPTION,
    CLAIM_DETAILS,
    CLAIM_ID,
    CLAIM_STATUS,
    CLAIM_SUBJECT,
    CLAIM_TYPE,
)
from graphrag.index.verbs.graph.report.restore_community_hierarchy import restore_community_hierarchy_df
from graphrag.index.verbs.graph.report.prepare_community_reports import prepare_community_reports_df
from graphrag.index.verbs.graph.report.create_community_reports import create_community_reports_df
from graphrag.index.cache import PipelineCache


@verb(name="create_final_community_reports", treats_input_tables_as_immutable=True)
async def create_final_community_reports(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
    covariates_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform community reports."""
    source = cast(pd.DataFrame, input.get_input())
    
    nodes = _prep_nodes(cast(pd.DataFrame, input.get_input()))
    edges = _prep_edges(cast(pd.DataFrame, get_required_input_table(input, "relationships").table))

    claims = None
    if covariates_enabled:
        claims = _prep_claims(cast(pd.DataFrame, get_required_input_table(input, "covariates").table))

    community_hierarchy = restore_community_hierarchy_df(
        nodes
    )

    local_contexts = prepare_community_reports_df(
        nodes, edges, claims, callbacks, strategy.get("max_input_length", 16_000)
    )

    community_reports = await create_community_reports_df(
        local_contexts,
        nodes,
        community_hierarchy,
        callbacks,
        cache,
        strategy,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    community_reports["id"] = community_reports["community"].apply(lambda _x: str(uuid4()))

    return create_verb_result(
        cast(
            Table,
            community_reports,
        )
    )


def _prep_nodes(input: pd.DataFrame) -> pd.DataFrame:
    input = input.fillna(value={NODE_DESCRIPTION: "No Description"})
    # merge values of four columns into a map column
    input[NODE_DETAILS] = input.apply(
        lambda x: {
            NODE_ID: x[NODE_ID],
            NODE_NAME: x[NODE_NAME],
            NODE_DESCRIPTION: x[NODE_DESCRIPTION],
            NODE_DEGREE: x[NODE_DEGREE],
        },
        axis=1,
    )
    return input


def _prep_edges(input: pd.DataFrame) -> pd.DataFrame:
    input = input.fillna(value={NODE_DESCRIPTION: "No Description"})
    input[EDGE_DETAILS] = input.apply(
        lambda x: {
            EDGE_ID: x[EDGE_ID],
            EDGE_SOURCE: x[EDGE_SOURCE],
            EDGE_TARGET: x[EDGE_TARGET],
            EDGE_DESCRIPTION: x[EDGE_DESCRIPTION],
            EDGE_DEGREE: x[EDGE_DEGREE],
        },
        axis=1,
    )
    return input


def _prep_claims(input: pd.DataFrame) -> pd.DataFrame:
    input = input.fillna(value={NODE_DESCRIPTION: "No Description"})
    input[CLAIM_DETAILS] = input.apply(
        lambda x: {
            CLAIM_ID: x[CLAIM_ID],
            CLAIM_SUBJECT: x[CLAIM_SUBJECT],
            CLAIM_TYPE: x[CLAIM_TYPE],
            CLAIM_STATUS: x[CLAIM_STATUS],
            CLAIM_DESCRIPTION: x[CLAIM_DESCRIPTION],
        },
        axis=1,
    )
    return input