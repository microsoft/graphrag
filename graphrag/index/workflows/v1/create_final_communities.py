# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_communities"


def build_steps(
    _config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final communities table.

    ## Dependencies
    * `workflow:create_base_entity_graph`
    """
    return [
        {
            "verb": "create_final_communities",
            "input": {"source": "workflow:create_base_entity_graph"},
        },
    ]
