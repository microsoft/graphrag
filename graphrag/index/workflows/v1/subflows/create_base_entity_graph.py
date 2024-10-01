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

from graphrag.index.storage import PipelineStorage
from graphrag.index.verbs.graph.clustering.cluster_graph import cluster_graph_df
from graphrag.index.verbs.graph.embed.embed_graph import embed_graph_df
from graphrag.index.verbs.snapshot_rows import snapshot_rows_df

from graphrag.index.flows.create_base_entity_graph import create_base_entity_graph as create_base_entity_graph_flow

@verb(
    name="create_base_entity_graph",
    treats_input_tables_as_immutable=True,
)
async def create_base_entity_graph(
    input: VerbInput,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    clustering_config: dict[str, Any],
    embedding_config: dict[str, Any],
    graphml_snapshot_enabled: bool = False,
    embed_graph_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create the base entity graph."""
    source = cast(pd.DataFrame, input.get_input())

    output = await create_base_entity_graph_flow(
        source,
        callbacks,
        storage,
        clustering_config,
        embedding_config,
        graphml_snapshot_enabled,
        embed_graph_enabled,
    )

    return create_verb_result(cast(Table, output))
