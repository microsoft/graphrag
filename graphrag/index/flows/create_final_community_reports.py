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
from graphrag.index.operations.embed_text import embed_text
from graphrag.index.operations.summarize_communities import (
    prepare_community_reports,
    restore_community_hierarchy,
    summarize_communities,
)


async def create_final_community_reports(
    nodes_input: pd.DataFrame,
    edges_input: pd.DataFrame,
    claims_input: pd.DataFrame | None,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    summarization_strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
    full_content_text_embed: dict | None = None,
    summary_text_embed: dict | None = None,
    title_text_embed: dict | None = None,
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

    # Embed full content if not skipped
    if full_content_text_embed:
        community_reports["full_content_embedding"] = await embed_text(
            community_reports,
            callbacks,
            cache,
            column="full_content",
            strategy=full_content_text_embed["strategy"],
            embedding_name="community_report_full_content",
        )

    # Embed summary if not skipped
    if summary_text_embed:
        community_reports["summary_embedding"] = await embed_text(
            community_reports,
            callbacks,
            cache,
            column="summary",
            strategy=summary_text_embed["strategy"],
            embedding_name="community_report_summary",
        )

    # Embed title if not skipped
    if title_text_embed:
        community_reports["title_embedding"] = await embed_text(
            community_reports,
            callbacks,
            cache,
            column="title",
            strategy=title_text_embed["strategy"],
            embedding_name="community_report_title",
        )

    return community_reports


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
