# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import networkx as nx

from graphrag.index.storage.memory_pipeline_storage import MemoryPipelineStorage
from graphrag.index.workflows.v1.create_base_entity_graph import (
    build_steps,
    workflow_name,
)

from .util import (
    get_config_for_workflow,
    get_workflow_output,
    load_expected,
    load_input_tables,
)


async def test_create_base_entity_graph():
    input_tables = load_input_tables([
        "workflow:create_summarized_entities",
    ])
    expected = load_expected(workflow_name)

    storage = MemoryPipelineStorage()

    config = get_config_for_workflow(workflow_name)

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
    actual_graphml_0 = actual["clustered_graph"][:1][0]
    actual_graph_0 = nx.parse_graphml(actual_graphml_0)

    expected_graphml_0 = expected["clustered_graph"][:1][0]
    expected_graph_0 = nx.parse_graphml(expected_graphml_0)

    assert (
        actual_graph_0.number_of_nodes() == expected_graph_0.number_of_nodes()
    ), "Graphml node count differs"
    assert (
        actual_graph_0.number_of_edges() == expected_graph_0.number_of_edges()
    ), "Graphml edge count differs"

    assert len(storage.keys()) == 0, "Storage should be empty"


async def test_create_base_entity_graph_with_embeddings():
    input_tables = load_input_tables([
        "workflow:create_summarized_entities",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["embed_graph_enabled"] = True

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    assert (
        len(actual.columns) == len(expected.columns) + 1
    ), "Graph dataframe missing embedding column"
    assert "embeddings" in actual.columns, "Graph dataframe missing embedding column"


async def test_create_base_entity_graph_with_snapshots():
    input_tables = load_input_tables([
        "workflow:create_summarized_entities",
    ])
    expected = load_expected(workflow_name)

    storage = MemoryPipelineStorage()

    config = get_config_for_workflow(workflow_name)

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
        "clustered_graph.0.graphml",
        "clustered_graph.1.graphml",
        "clustered_graph.2.graphml",
        "clustered_graph.3.graphml",
        "embedded_graph.0.graphml",
        "embedded_graph.1.graphml",
        "embedded_graph.2.graphml",
        "embedded_graph.3.graphml",
    ], "Graph snapshot keys differ"
