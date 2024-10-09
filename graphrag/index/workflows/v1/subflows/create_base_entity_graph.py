# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.flows.create_base_entity_graph import (
    create_base_entity_graph as create_base_entity_graph_flow,
)
from graphrag.index.storage import PipelineStorage


@verb(
    name="create_base_entity_graph",
    treats_input_tables_as_immutable=True,
)
async def create_base_entity_graph(
    input: VerbInput,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    clustering_strategy: dict[str, Any],
    embedding_strategy: dict[str, Any] | None,
    graphml_snapshot_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create the base entity graph."""
    source = cast(pd.DataFrame, input.get_input())

    output = await create_base_entity_graph_flow(
        source,
        callbacks,
        storage,
        clustering_strategy,
        embedding_strategy,
        graphml_snapshot_enabled=graphml_snapshot_enabled,
    )

    return create_verb_result(cast(Table, output))
