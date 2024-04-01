#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing build_steps method definition."""
from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

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
    _compute_top_level_node_positions = [
        {
            "verb": "unpack_graph",
            "args": {"column": "positioned_graph", "type": "nodes"},
            "input": {"source": "layed_out_entity_graph"},
        },
        {
            "verb": "filter",
            "args": {
                "column": "level",
                "criteria": [
                    {
                        "type": "value",
                        "operator": "equals",
                        "value": config.get("level_for_node_positions", "level_0"),
                    }
                ],
            },
        },
        {
            "verb": "select",
            "args": {"columns": ["id", "x", "y"]},
        },
        {
            "verb": "snapshot",
            "enabled": snapshot_top_level_nodes,
            "args": {
                "name": "top_level_nodes",
                "formats": ["json"],
            },
        },
        {
            "id": "_compute_top_level_node_positions",
            "verb": "rename",
            "args": {
                "columns": {
                    "id": "top_level_node_id",
                }
            },
        },
        {
            "verb": "convert",
            "args": {
                "column": "top_level_node_id",
                "to": "top_level_node_id",
                "type": "string",
            },
        },
    ]
    layout_graph_config = config.get(
        "layout_graph",
        {
            "strategy": {
                "type": "umap" if layout_graph_enabled else "zero",
            },
        },
    )
    return [
        {
            "id": "layed_out_entity_graph",
            "verb": "layout_graph",
            "args": {
                "embeddings_column": "embeddings",
                "graph_column": "clustered_graph",
                "to": "node_positions",
                "graph_to": "positioned_graph",
                **layout_graph_config,
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
        {
            "verb": "unpack_graph",
            "args": {"column": "positioned_graph", "type": "nodes"},
        },
        {
            "id": "nodes_without_positions",
            "verb": "drop",
            "args": {"columns": ["x", "y"]},
        },
        *_compute_top_level_node_positions,
        {
            "verb": "join",
            "args": {
                "on": ["id", "top_level_node_id"],
            },
            "input": {
                "source": "nodes_without_positions",
                "others": ["_compute_top_level_node_positions"],
            },
        },
        {
            "verb": "fill",
            "args": {
                "to": "type",
                "value": "entity",
            },
        },
        {
            "verb": "rename",
            "args": {"columns": {"label": "title", "cluster": "community"}},
        },
    ]
