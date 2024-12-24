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

from graphrag.config.models.embed_graph_config import EmbedGraphConfig
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

    embed_config = cast("EmbedGraphConfig", config.get("embed_graph"))

    return [
        {
            "verb": workflow_name,
            "args": {"layout_strategy": layout_strategy, "embed_config": embed_config},
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
    embed_config: EmbedGraphConfig,
    layout_strategy: dict[str, Any],
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
        embed_config=embed_config,
        layout_strategy=layout_strategy,
    )

    return create_verb_result(
        cast(
            "Table",
            output,
        )
    )
