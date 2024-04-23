import pandas as pd

import graphrag.index.verbs.graph.report.schemas as schemas
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
    """Sort context by degree in descending order.

    If max tokens is provided, we will return the context string that fits within the token limit.
    """

    def _get_context_string(
        entities: list[dict],
        edges: list[dict],
        claims: list[dict],
        sub_community_reports: list[dict] | None = None,
    ) -> str:
        """Concatenate structured data into a context string."""
        contexts = []
        if sub_community_reports:
            sub_community_reports = [
                report
                for report in sub_community_reports
                if community_id_column in report
                and report[community_id_column]
                and str(report[community_id_column]).strip() != ""
            ]
            report_df = pd.DataFrame(sub_community_reports).drop_duplicates()
            if not report_df.empty:
                if report_df[community_id_column].dtype == float:
                    report_df[community_id_column] = report_df[
                        community_id_column
                    ].astype(int)
                report_string = (
                    f"----Reports-----\n{report_df.to_csv(index=False, sep=',')}"
                )
                contexts.append(report_string)

        entities = [
            entity
            for entity in entities
            if node_id_column in entity
            and entity[node_id_column]
            and str(entity[node_id_column]).strip() != ""
        ]
        entity_df = pd.DataFrame(entities).drop_duplicates()
        if not entity_df.empty:
            if entity_df[node_id_column].dtype == float:
                entity_df[node_id_column] = entity_df[node_id_column].astype(int)
            entity_string = (
                f"-----Entities-----\n{entity_df.to_csv(index=False, sep=',')}"
            )
            contexts.append(entity_string)

        if claims and len(claims) > 0:
            claims = [
                claim
                for claim in claims
                if claim_id_column in claim
                and claim[claim_id_column]
                and str(claim[claim_id_column]).strip() != ""
            ]
            claim_df = pd.DataFrame(claims).drop_duplicates()
            if not claim_df.empty:
                if claim_df[claim_id_column].dtype == float:
                    claim_df[claim_id_column] = claim_df[claim_id_column].astype(int)
                claim_string = (
                    f"-----Claims-----\n{claim_df.to_csv(index=False, sep=',')}"
                )
                contexts.append(claim_string)

        edges = [
            edge
            for edge in edges
            if edge_id_column in edge
            and edge[edge_id_column]
            and str(edge[edge_id_column]).strip() != ""
        ]
        edge_df = pd.DataFrame(edges).drop_duplicates()
        if not edge_df.empty:
            if edge_df[edge_id_column].dtype == float:
                edge_df[edge_id_column] = edge_df[edge_id_column].astype(int)
            edge_string = (
                f"-----Relationships-----\n{edge_df.to_csv(index=False, sep=',')}"
            )
            contexts.append(edge_string)

        return "\n\n".join(contexts)

    # sort node details by degree in descending order
    edges = []
    node_details = {}
    claim_details = {}
    for record in local_context:
        edges.extend(record.get(edge_details_column, []))
        node_details[record[node_name_column]] = record[node_details_column]
        claim_details[record[node_name_column]] = record.get(claim_details_column, [])

    edges = [edge for edge in edges if isinstance(edge, dict)]
    edges = sorted(edges, key=lambda x: x[edge_degree_column], reverse=True)

    sorted_edges = []
    sorted_nodes = []
    sorted_claims = []
    context_string = ""
    for edge in edges:
        source_details = node_details.get(edge[edge_source_column], {})
        target_details = node_details.get(edge[edge_target_column], {})
        sorted_nodes.extend([source_details, target_details])
        sorted_edges.append(edge)
        source_claims = claim_details.get(edge[edge_source_column], [])
        target_claims = claim_details.get(edge[edge_target_column], [])
        sorted_claims.extend(source_claims if source_claims else [])
        sorted_claims.extend(target_claims if source_claims else [])
        if max_tokens:
            new_context_string = _get_context_string(
                sorted_nodes, sorted_edges, sorted_claims, sub_community_reports
            )
            if num_tokens(context_string) > max_tokens:
                break
            context_string = new_context_string

    if context_string == "":
        return _get_context_string(
            sorted_nodes, sorted_edges, sorted_claims, sub_community_reports
        )

    return context_string


def build_mixed_context(context: list[dict], max_tokens: int) -> str:
    """
    Build parent context by concatenating all sub-communities' contexts.

    If the context exceeds the limit, we use sub-community reports instead.
    """
    sorted_context = sorted(
        context, key=lambda x: x[schemas.CONTEXT_SIZE], reverse=True
    )

    # replace local context with sub-community reports, starting from the biggest sub-community
    substitute_reports = []
    final_local_contexts = []
    exceeded_limit = True
    context_string = ""

    for idx, sub_community_context in enumerate(sorted_context):
        if exceeded_limit:
            if sub_community_context[schemas.FULL_CONTENT]:
                substitute_reports.append({
                    schemas.COMMUNITY_ID: sub_community_context[schemas.SUB_COMMUNITY],
                    schemas.FULL_CONTENT: sub_community_context[schemas.FULL_CONTENT],
                })
            else:
                # this sub-community has no report, so we will use its local context
                final_local_contexts.extend(sub_community_context[schemas.ALL_CONTEXT])
                continue

            # add local context for the remaining sub-communities
            remaining_local_context = []
            for rid in range(idx + 1, len(sorted_context)):
                remaining_local_context.extend(sorted_context[rid][schemas.ALL_CONTEXT])
            new_context_string = sort_context(
                local_context=remaining_local_context + final_local_contexts,
                sub_community_reports=substitute_reports,
            )
            if num_tokens(new_context_string) <= max_tokens:
                exceeded_limit = False
                context_string = new_context_string
                break

    if exceeded_limit:
        # if all sub-community reports exceed the limit, we add reports until context is full
        substitute_reports = []
        for sub_community_context in sorted_context:
            substitute_reports.append({
                schemas.COMMUNITY_ID: sub_community_context[schemas.SUB_COMMUNITY],
                schemas.FULL_CONTENT: sub_community_context[schemas.FULL_CONTENT],
            })
            new_context_string = pd.DataFrame(substitute_reports).to_csv(
                index=False, sep=","
            )
            if num_tokens(new_context_string) > max_tokens:
                break

            context_string = new_context_string
    return context_string
