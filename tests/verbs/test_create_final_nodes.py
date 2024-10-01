# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.storage.memory_pipeline_storage import MemoryPipelineStorage
from graphrag.index.workflows.v1.create_final_nodes import (
    build_steps,
    workflow_name,
)

from .util import (
    compare_outputs,
    get_config_for_workflow,
    get_workflow_output,
    load_expected,
    load_input_tables,
)


async def test_create_final_nodes():
    input_tables = load_input_tables([
        "workflow:create_base_entity_graph",
    ])
    expected = load_expected(workflow_name)

    storage = MemoryPipelineStorage()

    config = get_config_for_workflow(workflow_name)

    # default config turns UMAP off, which translates into false for layout
    # we don't have graph embeddings in the test data, so this will fail if True
    config["layout_graph_enabled"] = False

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        storage=storage,
    )

    compare_outputs(actual, expected)

    assert len(storage.keys()) == 0, "Storage should be empty"


async def test_create_final_nodes_with_snapshot():
    input_tables = load_input_tables([
        "workflow:create_base_entity_graph",
    ])
    expected = load_expected(workflow_name)

    storage = MemoryPipelineStorage()

    config = get_config_for_workflow(workflow_name)

    # default config turns UMAP off, which translates into false for layout
    # we don't have graph embeddings in the test data, so this will fail if True
    config["layout_graph_enabled"] = False
    config["snapshot_top_level_nodes"] = True

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        storage=storage,
    )

    assert actual.shape == expected.shape, "Graph dataframe shapes differ"

    assert storage.keys() == [
        "top_level_nodes.json",
    ], "Graph snapshot keys differ"
