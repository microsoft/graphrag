# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.workflows.extract_graph_nlp import run_workflow

from tests.unit.config.utils import get_default_graphrag_config

from .util import (
    create_test_context,
)


async def test_extract_graph_nlp():
    context = await create_test_context(
        storage=["text_units"],
    )

    config = get_default_graphrag_config()

    await run_workflow(config, context)

    nodes_actual = await context.output_table_provider.read_dataframe("entities")
    edges_actual = await context.output_table_provider.read_dataframe("relationships")

    # this will be the raw count of entities and edges with no pruning
    # with NLP it is deterministic, so we can assert exact row counts
    assert len(nodes_actual) == 1147
    assert len(nodes_actual.columns) == 5
    assert len(edges_actual) == 29442
    assert len(edges_actual.columns) == 5
