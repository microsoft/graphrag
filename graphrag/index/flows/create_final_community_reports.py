# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform community reports."""

from uuid import uuid4

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.graph.extractors.community_reports.schemas import (
    CLAIM_DESCRIPTION,
    CLAIM_DETAILS,
    CLAIM_ID,
    CLAIM_STATUS,
    CLAIM_SUBJECT,
    CLAIM_TYPE,
    EDGE_DEGREE,
    EDGE_DESCRIPTION,
    EDGE_DETAILS,
    EDGE_ID,
    EDGE_SOURCE,
    EDGE_TARGET,
    NODE_DEGREE,
    NODE_DESCRIPTION,
    NODE_DETAILS,
    NODE_ID,
    NODE_NAME,
)
from graphrag.index.operations.summarize_communities import (
    prepare_community_reports,
    restore_community_hierarchy,
    summarize_communities,
)


async def create_final_community_reports(
    nodes_input: pd.DataFrame,
    edges_input: pd.DataFrame,
    communities_input: pd.DataFrame,
    claims_input: pd.DataFrame | None,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    summarization_strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
) -> pd.DataFrame:
    """All the steps to transform community reports."""
    nodes = _prep_nodes(nodes_input)
    edges = _prep_edges(edges_input)

    claims = None
    if claims_input is not None:
        claims = _prep_claims(claims_input)

    community_hierarchy = restore_community_hierarchy(nodes)

    local_contexts = prepare_community_reports(
        nodes,
        edges,
        claims,
        callbacks,
        summarization_strategy.get("max_input_length", 16_000),
    )

    community_reports = await summarize_communities(
        local_contexts,
        nodes,
        community_hierarchy,
        callbacks,
        cache,
        summarization_strategy,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    community_reports["id"] = community_reports["community"].apply(
        lambda _x: str(uuid4())
    )

    # Merge by community and it with communities to add size and period
    return community_reports.merge(
        communities_input.loc[:, ["id", "size", "period"]],
        left_on="community",
        right_on="id",
        how="left",
        copy=False,
        suffixes=("", "_y"),
    ).drop(columns=["id_y"])


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
