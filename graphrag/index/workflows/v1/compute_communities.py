# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import TYPE_CHECKING, cast

import pandas as pd
from datashaper import (
    Table,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.compute_communities import compute_communities
from graphrag.index.operations.snapshot import snapshot
from graphrag.storage.pipeline_storage import PipelineStorage

if TYPE_CHECKING:
    from graphrag.config.models.cluster_graph_config import ClusterGraphConfig

workflow_name = "compute_communities"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base communities from the graph edges.

    ## Dependencies
    * `workflow:extract_graph`
    """
    clustering_config = cast("ClusterGraphConfig", config.get("cluster_graph"))
    max_cluster_size = clustering_config.max_cluster_size
    use_lcc = clustering_config.use_lcc
    seed = clustering_config.seed

    snapshot_transient = config.get("snapshot_transient", False) or False

    return [
        {
            "verb": workflow_name,
            "args": {
                "max_cluster_size": max_cluster_size,
                "use_lcc": use_lcc,
                "seed": seed,
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
    max_cluster_size: int,
    use_lcc: bool,
    seed: int | None,
    snapshot_transient_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create the base entity graph."""
    base_relationship_edges = await runtime_storage.get("base_relationship_edges")

    base_communities = compute_communities(
        base_relationship_edges,
        max_cluster_size=max_cluster_size,
        use_lcc=use_lcc,
        seed=seed,
    )

    await runtime_storage.set("base_communities", base_communities)

    if snapshot_transient_enabled:
        await snapshot(
            base_communities,
            name="base_communities",
            storage=storage,
            formats=["parquet"],
        )

    return create_verb_result(cast("Table", pd.DataFrame()))
