# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.models.prune_graph_config import PruneGraphConfig
from graphrag.index.workflows.prune_graph import run_workflow

from tests.unit.config.utils import get_default_graphrag_config

from .util import (
    create_test_context,
)


async def test_prune_graph():
    context = await create_test_context(
        storage=["entities", "relationships"],
    )

    config = get_default_graphrag_config()
    config.prune_graph = PruneGraphConfig(
        min_node_freq=4, min_node_degree=0, min_edge_weight_pct=0
    )

    await run_workflow(config, context)

    nodes_actual = await context.output_table_provider.read_dataframe("entities")

    assert len(nodes_actual) == 29
