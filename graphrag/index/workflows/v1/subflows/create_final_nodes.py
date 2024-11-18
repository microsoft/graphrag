# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final nodes."""

from typing import Any, cast

from datashaper import (
    Table,
    VerbCallbacks,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.flows.create_final_nodes import (
    create_final_nodes as create_final_nodes_flow,
)
from graphrag.index.storage.pipeline_storage import PipelineStorage


@verb(name="create_final_nodes", treats_input_tables_as_immutable=True)
async def create_final_nodes(
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    runtime_storage: PipelineStorage,
    layout_strategy: dict[str, Any],
    level_for_node_positions: int,
    snapshot_top_level_nodes_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final nodes."""
    entity_graph = await runtime_storage.get("base_entity_graph")

    output = await create_final_nodes_flow(
        entity_graph,
        callbacks,
        storage,
        layout_strategy,
        level_for_node_positions,
        snapshot_top_level_nodes_enabled=snapshot_top_level_nodes_enabled,
    )

    return create_verb_result(
        cast(
            Table,
            output,
        )
    )
