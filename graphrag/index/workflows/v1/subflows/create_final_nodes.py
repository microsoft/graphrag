# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final nodes."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.flows.create_final_nodes import (
    create_final_nodes as create_final_nodes_flow,
)
from graphrag.index.storage import PipelineStorage


@verb(name="create_final_nodes", treats_input_tables_as_immutable=True)
async def create_final_nodes(
    input: VerbInput,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    strategy: dict[str, Any],
    level_for_node_positions: int,
    snapshot_top_level_nodes: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final nodes."""
    source = cast(pd.DataFrame, input.get_input())

    output = await create_final_nodes_flow(
        source,
        callbacks,
        storage,
        strategy,
        level_for_node_positions,
        snapshot_top_level_nodes,
    )

    return create_verb_result(
        cast(
            Table,
            output,
        )
    )
