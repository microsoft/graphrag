# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_community_reports"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final community reports table.

    ## Dependencies
    * `workflow:create_base_entity_graph`
    """
    covariates_enabled = config.get("covariates_enabled", False)
    create_community_reports_config = config.get("create_community_reports", {})
    base_text_embed = config.get("text_embed", {})
    community_report_full_content_embed_config = config.get(
        "community_report_full_content_embed", base_text_embed
    )
    community_report_summary_embed_config = config.get(
        "community_report_summary_embed", base_text_embed
    )
    community_report_title_embed_config = config.get(
        "community_report_title_embed", base_text_embed
    )
    skip_title_embedding = config.get("skip_title_embedding", False)
    skip_summary_embedding = config.get("skip_summary_embedding", False)
    skip_full_content_embedding = config.get("skip_full_content_embedding", False)

    return [
        #
        # Subworkflow: Prepare Nodes
        #
        {
            "id": "nodes",
            "verb": "prepare_community_reports_nodes",
            "input": {"source": "workflow:create_final_nodes"},
        },
        #
        # Subworkflow: Prepare Edges
        #
        {
            "id": "edges",
            "verb": "prepare_community_reports_edges",
            "input": {"source": "workflow:create_final_relationships"},
        },
        #
        # Subworkflow: Prepare Claims Table
        #
        {
            "id": "claims",
            "enabled": covariates_enabled,
            "verb": "prepare_community_reports_claims",
            "input": {
                "source": "workflow:create_final_covariates",
            }
            if covariates_enabled
            else {},
        },
        #
        # Subworkflow: Get Community Hierarchy
        #
        {
            "id": "community_hierarchy",
            "verb": "restore_community_hierarchy",
            "input": {"source": "nodes"},
        },
        #
        # Main Workflow: Create Community Reports
        #
        {
            "id": "local_contexts",
            "verb": "prepare_community_reports",
            "input": {
                "source": "nodes",
                "nodes": "nodes",
                "edges": "edges",
                **({"claims": "claims"} if covariates_enabled else {}),
            },
        },
        {
            "verb": "create_community_reports",
            "args": {
                **create_community_reports_config,
            },
            "input": {
                "source": "local_contexts",
                "community_hierarchy": "community_hierarchy",
                "nodes": "nodes",
            },
        },
        {
            # Generate a unique ID for each community report distinct from the community ID
            "verb": "window",
            "args": {"to": "id", "operation": "uuid", "column": "community"},
        },
        {
            "verb": "text_embed",
            "enabled": not skip_full_content_embedding,
            "args": {
                "embedding_name": "community_report_full_content",
                "column": "full_content",
                "to": "full_content_embedding",
                **community_report_full_content_embed_config,
            },
        },
        {
            "verb": "text_embed",
            "enabled": not skip_summary_embedding,
            "args": {
                "embedding_name": "community_report_summary",
                "column": "summary",
                "to": "summary_embedding",
                **community_report_summary_embed_config,
            },
        },
        {
            "verb": "text_embed",
            "enabled": not skip_title_embedding,
            "args": {
                "embedding_name": "community_report_title",
                "column": "title",
                "to": "title_embedding",
                **community_report_title_embed_config,
            },
        },
    ]
