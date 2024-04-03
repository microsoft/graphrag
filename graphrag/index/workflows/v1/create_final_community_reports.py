# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing build_steps method definition."""

from datashaper import AsyncType

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
    create_community_reports_config = config.get("create_community_reports", {})
    text_embed_config = config.get("text_embed", {})
    skip_title_embedding = config.get("skip_title_embedding", False)
    skip_summary_embedding = config.get("skip_summary_embedding", False)
    skip_full_content_embedding = config.get("skip_full_content_embedding", False)
    result = [
        {
            "verb": "prepare_community_reports",
            "args": {
                **create_community_reports_config,
                "graph_column": "clustered_graph",
                "async_mode": config.get("async_mode", AsyncType.AsyncIO),
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
        {
            "verb": "create_community_reports",
            "args": {
                **create_community_reports_config,
                "to": "community_report",
                "async_mode": create_community_reports_config.get(
                    "async_mode", AsyncType.AsyncIO
                ),
            },
        },
        {
            "verb": "select",
            "args": {
                "columns": [
                    "level",
                    "community_report",
                ]
            },
        },
        {
            "verb": "spread_json",
            "args": {
                "column": "community_report",
            },
        },
        {
            "verb": "rename",
            "args": {
                "columns": {
                    "community": "community_id",
                },
            },
        },
        {
            # Generate a unique ID for each community report distinct from the community ID
            "verb": "window",
            "args": {"to": "id", "operation": "uuid", "column": "community_id"},
        },
    ]

    if not skip_full_content_embedding:
        result.append({
            "verb": "text_embed",
            "args": {
                "column": "full_content",
                "to": "full_content_embedding",
                **text_embed_config,
            },
        })

    if not skip_summary_embedding:
        result.append({
            "verb": "text_embed",
            "args": {
                "column": "summary",
                "to": "summary_embedding",
                **text_embed_config,
            },
        })

    if not skip_title_embedding:
        result.append({
            "verb": "text_embed",
            "args": {
                "column": "title",
                "to": "title_embedding",
                **text_embed_config,
            },
        })

    return result
