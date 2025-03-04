# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.models.prune_graph_config import PruneGraphConfig
from graphrag.index.workflows.prune_graph import (
    run_workflow,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    create_test_context,
)


async def test_prune_graph():
    context = await create_test_context(
        storage=["entities", "relationships"],
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    config.prune_graph = PruneGraphConfig(
        min_node_freq=4, min_node_degree=0, min_edge_weight_pct=0
    )

    await run_workflow(config, context)

    nodes_actual = await load_table_from_storage("entities", context.storage)

    assert len(nodes_actual) == 21
