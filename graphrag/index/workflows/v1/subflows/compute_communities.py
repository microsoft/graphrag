# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    Table,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.flows.compute_communities import (
    compute_communities as compute_communities_flow,
)
from graphrag.storage.pipeline_storage import PipelineStorage


@verb(
    name="compute_communities",
    treats_input_tables_as_immutable=True,
)
async def compute_communities(
    storage: PipelineStorage,
    runtime_storage: PipelineStorage,
    clustering_strategy: dict[str, Any],
    snapshot_transient_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create the base entity graph."""
    base_relationship_edges = await runtime_storage.get("base_relationship_edges")

    base_communities = await compute_communities_flow(
        base_relationship_edges,
        storage,
        clustering_strategy=clustering_strategy,
        snapshot_transient_enabled=snapshot_transient_enabled,
    )

    await runtime_storage.set("base_communities", base_communities)

    return create_verb_result(cast("Table", pd.DataFrame()))
