# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.create_graphrag_config import create_graphrag_config
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

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})

    await run_workflow(config, context)

    nodes_actual = await load_table_from_storage("entities", context.storage)
    edges_actual = await load_table_from_storage("relationships", context.storage)

    assert len(nodes_actual) == 291
    assert len(edges_actual) == 452

    # x and y will be zero with the default configuration, because we do not embed/umap
    assert nodes_actual["x"].sum() == 0
    assert nodes_actual["y"].sum() == 0

    for column in ENTITIES_FINAL_COLUMNS:
        assert column in nodes_actual.columns
    for column in RELATIONSHIPS_FINAL_COLUMNS:
        assert column in edges_actual.columns


async def test_finalize_graph_umap():
    context = await _prep_tables()

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})

    config.embed_graph.enabled = True
    config.umap.enabled = True

    await run_workflow(config, context)

    nodes_actual = await load_table_from_storage("entities", context.storage)
    edges_actual = await load_table_from_storage("relationships", context.storage)

    assert len(nodes_actual) == 291
    assert len(edges_actual) == 452

    # x and y should have some value other than zero due to umap
    assert nodes_actual["x"].sum() != 0
    assert nodes_actual["y"].sum() != 0

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
    entities.drop(columns=["x", "y", "degree"], inplace=True)
    await write_table_to_storage(entities, "entities", context.storage)
    relationships = load_test_table("relationships")
    relationships.drop(columns=["combined_degree"], inplace=True)
    await write_table_to_storage(relationships, "relationships", context.storage)
    return context
