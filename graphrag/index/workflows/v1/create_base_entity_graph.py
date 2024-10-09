# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_base_entity_graph"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for the entity graph.

    ## Dependencies
    * `workflow:create_base_extracted_entities`
    """
    clustering_config = config.get(
        "cluster_graph",
        {"strategy": {"type": "leiden"}},
    )
    clustering_strategy = clustering_config.get("strategy")

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

    graphml_snapshot_enabled = config.get("graphml_snapshot", False) or False

    return [
        {
            "verb": "create_base_entity_graph",
            "args": {
                "clustering_strategy": clustering_strategy,
                "graphml_snapshot_enabled": graphml_snapshot_enabled,
                "embedding_strategy": embedding_strategy
                if embed_graph_enabled
                else None,
            },
            "input": ({"source": "workflow:create_summarized_entities"}),
        },
    ]
