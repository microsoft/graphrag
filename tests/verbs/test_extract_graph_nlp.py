# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.extract_graph_nlp import (
    run_workflow,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    create_test_context,
)


async def test_extract_graph_nlp():
    context = await create_test_context(
        storage=["text_units"],
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})

    await run_workflow(config, context)

    nodes_actual = await load_table_from_storage("entities", context.storage)
    edges_actual = await load_table_from_storage("relationships", context.storage)

    # this will be the raw count of entities and edges with no pruning
    # with NLP it is deterministic, so we can assert exact row counts
    assert len(nodes_actual) == 1148
    assert len(nodes_actual.columns) == 5
    assert len(edges_actual) == 29445
    assert len(edges_actual.columns) == 5
