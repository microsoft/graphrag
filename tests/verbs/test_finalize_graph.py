# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.data_model.schemas import (
    ENTITIES_FINAL_COLUMNS,
    RELATIONSHIPS_FINAL_COLUMNS,
)
from graphrag.index.workflows.finalize_graph import run_workflow

from tests.unit.config.utils import get_default_graphrag_config

from .util import (
    create_test_context,
    load_test_table,
)


async def test_finalize_graph():
    context = await _prep_tables()

    config = get_default_graphrag_config()

    await run_workflow(config, context)

    nodes_actual = await context.output_table_provider.read_dataframe("entities")
    edges_actual = await context.output_table_provider.read_dataframe("relationships")

    for column in ENTITIES_FINAL_COLUMNS:
        assert column in nodes_actual.columns
    for column in RELATIONSHIPS_FINAL_COLUMNS:
        assert column in edges_actual.columns


async def _prep_tables():
    context = await create_test_context(
        storage=["entities", "relationships"],
    )

    # edit the tables to eliminate final fields that wouldn't be on the inputs
    entities = load_test_table("entities")
    entities.drop(columns=["degree"], inplace=True)
    await context.output_table_provider.write_dataframe("entities", entities)
    relationships = load_test_table("relationships")
    relationships.drop(columns=["combined_degree"], inplace=True)
    await context.output_table_provider.write_dataframe("relationships", relationships)
    return context
