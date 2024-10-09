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
    summarization_strategy = create_community_reports_config.get("strategy")
    async_mode = create_community_reports_config.get("async_mode")
    num_threads = create_community_reports_config.get("num_threads")

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
    input = {
        "source": "workflow:create_final_nodes",
        "relationships": "workflow:create_final_relationships",
    }
    if covariates_enabled:
        input["covariates"] = "workflow:create_final_covariates"

    return [
        {
            "verb": "create_final_community_reports",
            "args": {
                "full_content_text_embed": community_report_full_content_embed_config
                if not skip_full_content_embedding
                else None,
                "summary_text_embed": community_report_summary_embed_config
                if not skip_summary_embedding
                else None,
                "title_text_embed": community_report_title_embed_config
                if not skip_title_embedding
                else None,
                "summarization_strategy": summarization_strategy,
                "async_mode": async_mode,
                "num_threads": num_threads,
            },
            "input": input,
        },
    ]
