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
from graphrag.storage.pipeline_storage import PipelineStorage


@verb(name="create_final_nodes", treats_input_tables_as_immutable=True)
async def create_final_nodes(
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

    output = create_final_nodes_flow(
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
