# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import Any, cast

from datashaper import (
    Table,
    VerbCallbacks,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_final_nodes import (
    create_final_nodes,
)
from graphrag.storage.pipeline_storage import PipelineStorage

workflow_name = "create_final_nodes"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for the document graph.

    ## Dependencies
    * `workflow:extract_graph`
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
            "verb": workflow_name,
            "args": {
                "layout_strategy": layout_strategy,
                "embedding_strategy": embedding_strategy
                if embed_graph_enabled
                else None,
            },
            "input": {
                "source": "workflow:extract_graph",
                "communities": "workflow:compute_communities",
            },
        },
    ]


@verb(name=workflow_name, treats_input_tables_as_immutable=True)
async def workflow(
    callbacks: VerbCallbacks,
    runtime_storage: PipelineStorage,
    layout_strategy: dict[str, Any],
    embedding_strategy: dict[str, Any] | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final nodes."""
    base_entity_nodes = await runtime_storage.get("base_entity_nodes")
    base_relationship_edges = await runtime_storage.get("base_relationship_edges")
    base_communities = await runtime_storage.get("base_communities")

    output = create_final_nodes(
        base_entity_nodes,
        base_relationship_edges,
        base_communities,
        callbacks,
        layout_strategy,
        embedding_strategy=embedding_strategy,
    )

    return create_verb_result(
        cast(
            "Table",
            output,
        )
    )
