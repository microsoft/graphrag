# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import networkx as nx

from graphrag.index.storage.memory_pipeline_storage import MemoryPipelineStorage
from graphrag.index.workflows.v1.create_summarized_entities import (
    build_steps,
    workflow_name,
)

from .util import (
    get_config_for_workflow,
    get_workflow_output,
    load_expected,
    load_input_tables,
)


async def test_create_summarized_entities():
    input_tables = load_input_tables([
        "workflow:create_base_extracted_entities",
    ])
    expected = load_expected(workflow_name)

    storage = MemoryPipelineStorage()

    config = get_config_for_workflow(workflow_name)

    del config["summarize_descriptions"]["strategy"]["llm"]

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        storage=storage,
    )

    # the serialization of the graph may differ so we can't assert the dataframes directly
    assert actual.shape == expected.shape, "Graph dataframe shapes differ"

    # let's parse a sample of the raw graphml
    actual_graphml_0 = actual["entity_graph"][:1][0]
    actual_graph_0 = nx.parse_graphml(actual_graphml_0)

    expected_graphml_0 = expected["entity_graph"][:1][0]
    expected_graph_0 = nx.parse_graphml(expected_graphml_0)

    assert (
        actual_graph_0.number_of_nodes() == expected_graph_0.number_of_nodes()
    ), "Graphml node count differs"
    assert (
        actual_graph_0.number_of_edges() == expected_graph_0.number_of_edges()
    ), "Graphml edge count differs"

    # ensure the mock summary was injected to the nodes
    nodes = list(actual_graph_0.nodes(data=True))
    assert (
        nodes[0][1]["description"]
        == "This is a MOCK response for the LLM. It is summarized!"
    )

    assert len(storage.keys()) == 0, "Storage should be empty"


async def test_create_summarized_entities_with_snapshots():
    input_tables = load_input_tables([
        "workflow:create_base_extracted_entities",
    ])
    expected = load_expected(workflow_name)

    storage = MemoryPipelineStorage()

    config = get_config_for_workflow(workflow_name)

    del config["summarize_descriptions"]["strategy"]["llm"]
    config["graphml_snapshot"] = True

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
        "summarized_graph.graphml",
    ], "Graph snapshot keys differ"
