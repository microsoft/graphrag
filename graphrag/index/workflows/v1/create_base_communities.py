# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_base_communities"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base communities from the graph edges.

    ## Dependencies
    * `workflow:create_base_entity_graph`
    """
    clustering_config = config.get(
        "cluster_graph",
        {"strategy": {"type": "leiden"}},
    )
    clustering_strategy = clustering_config.get("strategy")

    snapshot_transient = config.get("snapshot_transient", False) or False

    return [
        {
            "verb": "create_base_communities",
            "args": {
                "clustering_strategy": clustering_strategy,
                "snapshot_transient_enabled": snapshot_transient,
            },
            "input": ({"source": "workflow:create_base_entity_graph"}),
        },
    ]
