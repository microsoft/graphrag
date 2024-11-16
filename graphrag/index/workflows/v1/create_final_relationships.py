# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

import logging

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_relationships"

log = logging.getLogger(__name__)


def build_steps(
    config: PipelineWorkflowConfig,  # noqa: ARG001
) -> list[PipelineWorkflowStep]:
    """
    Create the final relationships table.

    ## Dependencies
    * `workflow:create_base_entity_graph`
    * `workflow:create_final_nodes`
    """
    return [
        {
            "verb": "create_final_relationships",
            "args": {},
            "input": {
                "source": "workflow:create_base_entity_graph",
                "nodes": "workflow:create_final_nodes",
            },
        },
    ]
