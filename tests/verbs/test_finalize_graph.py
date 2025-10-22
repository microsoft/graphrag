# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.schemas import (
    ENTITIES_FINAL_COLUMNS,
    RELATIONSHIPS_FINAL_COLUMNS,
)
from graphrag.index.workflows.finalize_graph import (
    run_workflow,
)
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    create_test_context,
    load_test_table,
)


async def test_finalize_graph():
    context = await _prep_tables()

    config = GraphRagConfig(models=DEFAULT_MODEL_CONFIG)  # type: ignore

    await run_workflow(config, context)

    nodes_actual = await load_table_from_storage("entities", context.output_storage)
    edges_actual = await load_table_from_storage(
        "relationships", context.output_storage
    )

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
    await write_table_to_storage(entities, "entities", context.output_storage)
    relationships = load_test_table("relationships")
    relationships.drop(columns=["combined_degree"], inplace=True)
    await write_table_to_storage(relationships, "relationships", context.output_storage)
    return context
