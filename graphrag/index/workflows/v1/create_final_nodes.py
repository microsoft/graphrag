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

    embed_graph_config = config.get(
        "embed_graph",
        {
            "strategy": {
                "type": "node2vec",
                "num_walks": config.get("embed_num_walks", 10),
                "walk_length": config.get("embed_walk_length", 40),
                "window_size": config.get("embed_window_size", 2),
                "iterations": config.get("embed_iterations", 3),
                "random_seed": config.get("embed_random_seed", 86),
            }
        },
    )
    embedding_strategy = embed_graph_config.get("strategy")
    embed_graph_enabled = config.get("embed_graph_enabled", False) or False

    return [
        {
            "verb": "create_final_nodes",
            "args": {
                "layout_strategy": layout_strategy,
                "embedding_strategy": embedding_strategy
                if embed_graph_enabled
                else None,
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
    ]
