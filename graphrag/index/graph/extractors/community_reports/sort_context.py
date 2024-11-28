# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Sort context by degree in descending order."""

import pandas as pd

import graphrag.index.graph.extractors.community_reports.schemas as schemas
from graphrag.query.llm.text_utils import num_tokens


def sort_context(
    local_context: list[dict],
    sub_community_reports: list[dict] | None = None,
    max_tokens: int | None = None,
    node_id_column: str = schemas.NODE_ID,
    node_name_column: str = schemas.NODE_NAME,
    node_details_column: str = schemas.NODE_DETAILS,
    edge_id_column: str = schemas.EDGE_ID,
    edge_details_column: str = schemas.EDGE_DETAILS,
    edge_degree_column: str = schemas.EDGE_DEGREE,
    edge_source_column: str = schemas.EDGE_SOURCE,
    edge_target_column: str = schemas.EDGE_TARGET,
    claim_id_column: str = schemas.CLAIM_ID,
    claim_details_column: str = schemas.CLAIM_DETAILS,
    community_id_column: str = schemas.COMMUNITY_ID,
) -> str:
    """Optimized sorting and formatting of context data."""

    # Preprocess local_context into DataFrames
    context_df = pd.DataFrame(local_context)
    edges = context_df[edge_details_column].explode().dropna()
    nodes = context_df[[node_name_column, node_details_column]].drop_duplicates()
    claims = context_df[claim_details_column].explode().dropna()

    # Filter and deduplicate
    edges_df = pd.DataFrame(edges.tolist()).drop_duplicates()
    nodes_df = pd.DataFrame(nodes).drop_duplicates()
    claims_df = pd.DataFrame(claims.tolist()).drop_duplicates()

    # Pre-sort edges by degree descending
    if not edges_df.empty:
        edges_df = edges_df.sort_values(by=edge_degree_column, ascending=False)

    # Group and map claims/nodes to edges
    edges_df['source_details'] = edges_df[edge_source_column].map(
        nodes_df.set_index(node_name_column)[node_details_column].to_dict()
    )
    edges_df['target_details'] = edges_df[edge_target_column].map(
        nodes_df.set_index(node_name_column)[node_details_column].to_dict()
    )
    edges_df['source_claims'] = edges_df[edge_source_column].map(
        claims_df.set_index(claim_id_column).to_dict(orient="list")
    )
    edges_df['target_claims'] = edges_df[edge_target_column].map(
        claims_df.set_index(claim_id_column).to_dict(orient="list")
    )

    # Concatenate structured data into context string
    def _generate_context_string():
        contexts = []
        if sub_community_reports:
            report_df = pd.DataFrame(sub_community_reports).drop_duplicates()
            if not report_df.empty:
                contexts.append(
                    f"----Reports-----\n{report_df.to_csv(index=False, sep=',')}"
                )
        if not nodes_df.empty:
            contexts.append(
                f"-----Entities-----\n{nodes_df.to_csv(index=False, sep=',')}"
            )
        if not edges_df.empty:
            contexts.append(
                f"-----Relationships-----\n{edges_df.to_csv(index=False, sep=',')}"
            )
        if not claims_df.empty:
            contexts.append(
                f"-----Claims-----\n{claims_df.to_csv(index=False, sep=',')}"
            )
        return "\n\n".join(contexts)

    context_string = _generate_context_string()

    # Enforce token constraints
    if max_tokens:
        while num_tokens(context_string) > max_tokens and not edges_df.empty:
            edges_df = edges_df.iloc[:-1]  # Remove the least significant edge
            context_string = _generate_context_string()

    return context_string



def sort_context_batch(
    local_contexts: pd.DataFrame,
    node_id_column: str,
    node_name_column: str,
    node_details_column: str,
    edge_id_column: str,
    edge_details_column: str,
    edge_degree_column: str,
    edge_source_column: str,
    edge_target_column: str,
    claim_id_column: str,
    claim_details_column: str,
    community_id_column: str,
    max_tokens: int | None = None,
) -> pd.DataFrame:
    """Batch processing for community context strings."""

    def generate_context(group):
        # Explode and deduplicate edges and claims
        edges = pd.DataFrame(group[edge_details_column].explode().dropna().tolist())
        claims = pd.DataFrame(group[claim_details_column].dropna().tolist())
        nodes = pd.DataFrame(group[node_details_column].dropna().tolist())

        # Pre-sort edges by degree descending
        if not edges.empty:
            edges = edges.sort_values(by=edge_degree_column, ascending=False)

        # Generate context string
        contexts = []
        if not nodes.empty and len(nodes) > 1:
            contexts.append(f"-----Entities-----\n{nodes.to_csv(index=False, sep=',')}")
        if not edges.empty and len(edges) > 1:
            contexts.append(f"-----Relationships-----\n{edges.to_csv(index=False, sep=',')}")
        if not claims.empty and len(claims) > 1:
            contexts.append(f"-----Claims-----\n{claims.to_csv(index=False, sep=',')}")

        context_string = "\n\n".join(contexts)
        context_string_len = num_tokens(context_string)

        return pd.Series({
            schemas.CONTEXT_STRING: context_string,
            schemas.CONTEXT_SIZE: context_string_len,
            schemas.CONTEXT_EXCEED_FLAG: context_string_len > max_tokens if max_tokens else False,
            schemas.ALL_CONTEXT: group[schemas.ALL_CONTEXT].tolist()
        })

    # Group by community and process in bulk
    context_results = local_contexts.groupby(community_id_column).apply(generate_context)

    # Return a DataFrame with the results
    return context_results.reset_index()