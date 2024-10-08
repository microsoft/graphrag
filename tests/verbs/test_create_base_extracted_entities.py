# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import networkx as nx

from graphrag.index.storage.memory_pipeline_storage import MemoryPipelineStorage
from graphrag.index.workflows.v1.create_base_extracted_entities import (
    build_steps,
    workflow_name,
)

from .util import (
    get_config_for_workflow,
    get_workflow_output,
    load_expected,
    load_input_tables,
)


async def test_create_base_extracted_entities():
    input_tables = load_input_tables(["workflow:create_base_text_units"])
    expected = load_expected(workflow_name)

    storage = MemoryPipelineStorage()

    config = get_config_for_workflow(workflow_name)

    del config["entity_extract"]["strategy"]["llm"]

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        storage=storage,
    )

    # let's parse a sample of the raw graphml
    actual_graphml_0 = actual["entity_graph"][:1][0]
    actual_graph_0 = nx.parse_graphml(actual_graphml_0)

    assert actual_graph_0.number_of_nodes() == 3
    assert actual_graph_0.number_of_edges() == 2

    assert actual.columns == expected.columns

    assert len(storage.keys()) == 0, "Storage should be empty"


async def test_create_base_extracted_entities_with_snapshots():
    input_tables = load_input_tables(["workflow:create_base_text_units"])
    expected = load_expected(workflow_name)

    storage = MemoryPipelineStorage()

    config = get_config_for_workflow(workflow_name)

    del config["entity_extract"]["strategy"]["llm"]
    config["raw_entity_snapshot"] = True
    config["graphml_snapshot"] = True

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        storage=storage,
    )

    print(storage.keys())

    assert actual.columns == expected.columns

    assert storage.keys() == ["raw_extracted_entities.json", "merged_graph.graphml"]
