# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Sort context by degree in descending order."""

import pandas as pd

import graphrag.data_model.schemas as schemas
from graphrag.query.llm.text_utils import num_tokens


def sort_context(
    local_context: list[dict],
    sub_community_reports: list[dict] | None = None,
    max_context_tokens: int | None = None,
    node_name_column: str = schemas.TITLE,
    node_details_column: str = schemas.NODE_DETAILS,
    edge_id_column: str = schemas.SHORT_ID,
    edge_details_column: str = schemas.EDGE_DETAILS,
    edge_degree_column: str = schemas.EDGE_DEGREE,
    edge_source_column: str = schemas.EDGE_SOURCE,
    edge_target_column: str = schemas.EDGE_TARGET,
    claim_details_column: str = schemas.CLAIM_DETAILS,
) -> str:
    """Sort context by degree in descending order, optimizing for performance."""

    def _get_context_string(
        entities: list[dict],
        edges: list[dict],
        claims: list[dict],
        sub_community_reports: list[dict] | None = None,
    ) -> str:
        """Concatenate structured data into a context string."""
        contexts = []
        if sub_community_reports:
            report_df = pd.DataFrame(sub_community_reports)
            if not report_df.empty:
                contexts.append(
                    f"----Reports-----\n{report_df.to_csv(index=False, sep=',')}"
                )

        for label, data in [
            ("Entities", entities),
            ("Claims", claims),
            ("Relationships", edges),
        ]:
            if data:
                data_df = pd.DataFrame(data)
                if not data_df.empty:
                    contexts.append(
                        f"-----{label}-----\n{data_df.to_csv(index=False, sep=',')}"
                    )

        return "\n\n".join(contexts)

    # Preprocess local context
    edges = [
        {**e, schemas.SHORT_ID: int(e[schemas.SHORT_ID])}
        for record in local_context
        for e in record.get(edge_details_column, [])
        if isinstance(e, dict)
    ]

    node_details = {
        record[node_name_column]: {
            **record[node_details_column],
            schemas.SHORT_ID: int(record[node_details_column][schemas.SHORT_ID]),
        }
        for record in local_context
    }

    claim_details = {
        record[node_name_column]: [
            {**c, schemas.SHORT_ID: int(c[schemas.SHORT_ID])}
            for c in record.get(claim_details_column, [])
            if isinstance(c, dict) and c.get(schemas.SHORT_ID) is not None
        ]
        for record in local_context
        if isinstance(record.get(claim_details_column), list)
    }

    # Sort edges by degree (desc) and ID (asc)
    edges.sort(key=lambda x: (-x.get(edge_degree_column, 0), x.get(edge_id_column, "")))

    # Deduplicate and build context incrementally
    edge_ids, nodes_ids, claims_ids = set(), set(), set()
    sorted_edges, sorted_nodes, sorted_claims = [], [], []
    context_string = ""

    for edge in edges:
        source, target = edge[edge_source_column], edge[edge_target_column]

        # Add source and target node details
        for node in [node_details.get(source), node_details.get(target)]:
            if node and node[schemas.SHORT_ID] not in nodes_ids:
                nodes_ids.add(node[schemas.SHORT_ID])
                sorted_nodes.append(node)

        # Add claims related to source and target
        for claims in [claim_details.get(source), claim_details.get(target)]:
            if claims:
                for claim in claims:
                    if claim[schemas.SHORT_ID] not in claims_ids:
                        claims_ids.add(claim[schemas.SHORT_ID])
                        sorted_claims.append(claim)

        # Add the edge
        if edge[schemas.SHORT_ID] not in edge_ids:
            edge_ids.add(edge[schemas.SHORT_ID])
            sorted_edges.append(edge)

        # Generate new context string
        new_context_string = _get_context_string(
            sorted_nodes, sorted_edges, sorted_claims, sub_community_reports
        )
        if max_context_tokens and num_tokens(new_context_string) > max_context_tokens:
            break
        context_string = new_context_string

    # Return the final context string
    return context_string or _get_context_string(
        sorted_nodes, sorted_edges, sorted_claims, sub_community_reports
    )


def parallel_sort_context_batch(community_df, max_context_tokens, parallel=False):
    """Calculate context using parallelization if enabled."""
    if parallel:
        # Use ThreadPoolExecutor for parallel execution
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=None) as executor:
            context_strings = list(
                executor.map(
                    lambda x: sort_context(x, max_context_tokens=max_context_tokens),
                    community_df[schemas.ALL_CONTEXT],
                )
            )
        community_df[schemas.CONTEXT_STRING] = context_strings

    else:
        # Assign context strings directly to the DataFrame
        community_df[schemas.CONTEXT_STRING] = community_df[schemas.ALL_CONTEXT].apply(
            lambda context_list: sort_context(
                context_list, max_context_tokens=max_context_tokens
            )
        )

    # Calculate other columns
    community_df[schemas.CONTEXT_SIZE] = community_df[schemas.CONTEXT_STRING].apply(
        num_tokens
    )
    community_df[schemas.CONTEXT_EXCEED_FLAG] = (
        community_df[schemas.CONTEXT_SIZE] > max_context_tokens
    )

    return community_df
