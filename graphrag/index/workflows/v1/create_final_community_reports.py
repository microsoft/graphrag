# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep

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

    input = {
        "source": "workflow:create_final_nodes",
        "relationships": "workflow:create_final_relationships",
        "entities": "workflow:create_final_entities",
        "communities": "workflow:create_final_communities",
    }
    if covariates_enabled:
        input["covariates"] = "workflow:create_final_covariates"

    return [
        {
            "verb": "create_final_community_reports",
            "args": {
                "summarization_strategy": summarization_strategy,
                "async_mode": async_mode,
                "num_threads": num_threads,
            },
            "input": input,
        },
    ]
