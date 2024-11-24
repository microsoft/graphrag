# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_nodes"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for the document graph.

    ## Dependencies
    * `workflow:create_base_entity_graph`
    """
    snapshot_top_level_nodes = config.get("snapshot_top_level_nodes", False)
    layout_graph_enabled = config.get("layout_graph_enabled", True)
    layout_graph_config = config.get(
        "layout_graph",
        {
            "strategy": {
                "type": "umap" if layout_graph_enabled else "zero",
            },
        },
    )
    layout_strategy = layout_graph_config.get("strategy")
    level_for_node_positions = config.get("level_for_node_positions", 0)

    return [
        {
            "id": "laid_out_entity_graph",
            "verb": "create_final_nodes",
            "args": {
                "layout_strategy": layout_strategy,
                "level_for_node_positions": level_for_node_positions,
                "snapshot_top_level_nodes_enabled": snapshot_top_level_nodes,
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
    ]
