# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing create_community_reports and load_strategy methods definition."""

import logging
from enum import Enum
from typing import cast

import pandas as pd
from datashaper import (
    TableContainer,
    VerbCallbacks,
    VerbInput,
    progress_iterable,
    verb,
)

import graphrag.index.graph.extractors.community_reports.schemas as schemas
from graphrag.index.graph.extractors.community_reports import sort_context
from graphrag.query.llm.text_utils import num_tokens

log = logging.getLogger(__name__)

_NAMED_INPUTS_REQUIRED = "Named inputs are required"


class CreateCommunityReportsStrategyType(str, Enum):
    """CreateCommunityReportsStrategyType class definition."""

    graph_intelligence = "graph_intelligence"


_DEFAULT_MISSING_DESCRIPTION_TEXT = "No Description"


@verb(name="build_community_local_contexts")
def build_community_local_contexts(
    input: VerbInput,
    callbacks: VerbCallbacks,
    max_tokens: int = 16_000,
    community_id_column: str = schemas.COMMUNITY_ID,
    node_id_column: str = schemas.NODE_ID,
    node_name_column: str = schemas.NODE_NAME,
    node_details_column: str = schemas.NODE_DETAILS,
    node_description_column: str = schemas.NODE_DESCRIPTION,
    node_level_column: str = schemas.NODE_LEVEL,
    node_degree_column: str = schemas.NODE_DEGREE,
    node_community_column: str = schemas.NODE_COMMUNITY,
    edge_id_column: str = schemas.EDGE_ID,
    edge_source_column: str = schemas.EDGE_SOURCE,
    edge_target_column: str = schemas.EDGE_TARGET,
    edge_degree_column: str = schemas.EDGE_DEGREE,
    edge_details_column: str = schemas.EDGE_DETAILS,
    claim_id_column: str = schemas.CLAIM_ID,
    claim_subject_column: str = schemas.CLAIM_SUBJECT,
    claim_details_column: str = schemas.CLAIM_DETAILS,
    **_kwargs,
) -> TableContainer:
    """Generate entities for each row, and optionally a graph of those entities."""
    named_inputs = input.named
    if named_inputs is None:
        raise ValueError(_NAMED_INPUTS_REQUIRED)

    def get_table(name: str) -> pd.DataFrame:
        container = named_inputs.get(name)
        if container is None:
            msg = f"Missing input: {name}"
            raise ValueError(msg)
        return cast(pd.DataFrame, container.table)

    def _prep_node_details(
        node_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Concatenate node details."""
        node_df = node_df.fillna(
            value={node_description_column: _DEFAULT_MISSING_DESCRIPTION_TEXT}
        )

        # merge values of four columns into a map column
        node_df[node_details_column] = node_df.apply(
            lambda x: {
                node_id_column: x[node_id_column],
                node_name_column: x[node_name_column],
                node_description_column: x[node_description_column],
                node_degree_column: x[node_degree_column],
            },
            axis=1,
        )
        return node_df

    def _prep_local_context(
        node_df: pd.DataFrame,
        edge_df: pd.DataFrame,
        claim_df: pd.DataFrame,
        max_tokens: int,
    ) -> pd.DataFrame:
        levels = sorted(node_df[node_level_column].unique().tolist())
        dfs = []
        for level in progress_iterable(levels, callbacks.progress, len(levels)):
            level_node_df = cast(
                pd.DataFrame, node_df[node_df[node_level_column] == level]
            )
            level_node_df = _prep_node_details(level_node_df)
            log.info("Number of nodes at level %s", len(level_node_df))

            # filter edges to those with source and target nodes at the current level
            nodes = level_node_df[node_name_column].tolist()
            level_edge_df = edge_df[
                edge_df[edge_source_column].isin(nodes)
                & edge_df[edge_target_column].isin(nodes)
            ]

            # concat all edge details per node
            merged_source_node_df = level_node_df.merge(
                cast(
                    pd.DataFrame,
                    level_edge_df[[edge_source_column, edge_details_column]],
                ).rename(columns={edge_source_column: node_name_column}),
                on=node_name_column,
                how="left",
            )
            merged_target_node_df = level_node_df.merge(
                cast(
                    pd.DataFrame,
                    level_edge_df[[edge_target_column, edge_details_column]],
                ).rename(columns={edge_target_column: node_name_column}),
                on=node_name_column,
                how="left",
            )
            merged_node_df = pd.concat(
                [merged_source_node_df, merged_target_node_df], axis=0
            )
            merged_node_df = (
                merged_node_df.groupby([
                    node_name_column,
                    node_community_column,
                    node_degree_column,
                ])
                .agg({node_details_column: "first", edge_details_column: list})
                .reset_index()
            )

            # concat all claim details per node
            if claim_df is not None:
                level_claim_df = claim_df[claim_df[claim_subject_column].isin(nodes)]
                merged_node_df = merged_node_df.merge(
                    cast(
                        pd.DataFrame,
                        level_claim_df[[claim_subject_column, claim_details_column]],
                    ).rename(columns={claim_subject_column: node_name_column}),
                    on=node_name_column,
                    how="left",
                )
                merged_node_df = (
                    merged_node_df.groupby([
                        node_name_column,
                        node_community_column,
                        node_level_column,
                        node_degree_column,
                    ])
                    .agg({
                        node_details_column: "first",
                        edge_details_column: "first",
                        claim_details_column: list,
                    })
                    .reset_index()
                )
            else:
                merged_node_df[claim_details_column] = None

            # concat all node details, including name, degree, node_details, edge_details, and claim_details
            merged_node_df[schemas.ALL_CONTEXT] = merged_node_df.apply(
                lambda x: {
                    node_name_column: x[node_name_column],
                    node_degree_column: x[node_degree_column],
                    node_details_column: x[node_details_column],
                    edge_details_column: x[edge_details_column],
                    claim_details_column: x[claim_details_column],
                },
                axis=1,
            )

            # group all node details by community
            community_df = (
                merged_node_df.groupby(node_community_column)
                .agg({schemas.ALL_CONTEXT: list})
                .reset_index()
            )
            community_df[schemas.CONTEXT_STRING] = community_df[
                schemas.ALL_CONTEXT
            ].apply(
                lambda x: sort_context(
                    x,
                    node_id_column=node_id_column,
                    node_name_column=node_name_column,
                    node_details_column=node_details_column,
                    edge_id_column=edge_id_column,
                    edge_details_column=edge_details_column,
                    edge_degree_column=edge_degree_column,
                    edge_source_column=edge_source_column,
                    edge_target_column=edge_target_column,
                    claim_id_column=claim_id_column,
                    claim_details_column=claim_details_column,
                    community_id_column=community_id_column,
                )
            )
            community_df[schemas.CONTEXT_SIZE] = community_df[
                schemas.CONTEXT_STRING
            ].apply(lambda x: num_tokens(x))
            community_df[schemas.CONTEXT_EXCEED_FLAG] = community_df[
                schemas.CONTEXT_SIZE
            ].apply(lambda x: x > max_tokens)
            community_df[schemas.COMMUNITY_LEVEL] = level
            dfs.append(community_df)

        return pd.concat(dfs)

    # Prepare Community Reports
    nodes = get_table("nodes")
    edges = get_table("edges")
    claims = get_table("claims")
    # build initial local context for all communities
    local_contexts = _prep_local_context(nodes, edges, claims, max_tokens)
    return TableContainer(table=local_contexts)
