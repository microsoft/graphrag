# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.models.graph_rag_config import GraphRagConfig
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

    config = GraphRagConfig(models=DEFAULT_MODEL_CONFIG)  # type: ignore

    await run_workflow(config, context)

    nodes_actual = await load_table_from_storage("entities", context.output_storage)
    edges_actual = await load_table_from_storage(
        "relationships", context.output_storage
    )

    # this will be the raw count of entities and edges with no pruning
    # with NLP it is deterministic, so we can assert exact row counts
    assert len(nodes_actual) == 1147
    assert len(nodes_actual.columns) == 5
    assert len(edges_actual) == 29442
    assert len(edges_actual.columns) == 5
