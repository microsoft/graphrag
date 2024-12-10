# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    Table,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.compute_communities import compute_communities
from graphrag.storage.pipeline_storage import PipelineStorage

workflow_name = "compute_communities"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base communities from the graph edges.

    ## Dependencies
    * `workflow:extract_graph`
    """
    clustering_config = config.get(
        "cluster_graph",
        {"strategy": {"type": "leiden"}},
    )
    clustering_strategy = clustering_config.get("strategy")

    snapshot_transient = config.get("snapshot_transient", False) or False

    return [
        {
            "verb": workflow_name,
            "args": {
                "clustering_strategy": clustering_strategy,
                "snapshot_transient_enabled": snapshot_transient,
            },
            "input": ({"source": "workflow:extract_graph"}),
        },
    ]


@verb(
    name=workflow_name,
    treats_input_tables_as_immutable=True,
)
async def workflow(
    storage: PipelineStorage,
    runtime_storage: PipelineStorage,
    clustering_strategy: dict[str, Any],
    snapshot_transient_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create the base entity graph."""
    base_relationship_edges = await runtime_storage.get("base_relationship_edges")

    base_communities = await compute_communities(
        base_relationship_edges,
        storage,
        clustering_strategy=clustering_strategy,
        snapshot_transient_enabled=snapshot_transient_enabled,
    )

    await runtime_storage.set("base_communities", base_communities)

    return create_verb_result(cast("Table", pd.DataFrame()))
