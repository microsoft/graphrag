# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import pytest

from graphrag.config.enums import LLMType
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.create_base_entity_graph import (
    build_steps,
    workflow_name,
)

from .util import (
    get_config_for_workflow,
    get_workflow_output,
    load_input_tables,
    load_test_table,
)

MOCK_LLM_ENTITY_RESPONSES = [
    """
    ("entity"<|>COMPANY_A<|>COMPANY<|>Company_A is a test company)
    ##
    ("entity"<|>COMPANY_B<|>COMPANY<|>Company_B owns Company_A and also shares an address with Company_A)
    ##
    ("entity"<|>PERSON_C<|>PERSON<|>Person_C is director of Company_A)
    ##
    ("relationship"<|>COMPANY_A<|>COMPANY_B<|>Company_A and Company_B are related because Company_A is 100% owned by Company_B and the two companies also share the same address)<|>2)
    ##
    ("relationship"<|>COMPANY_A<|>PERSON_C<|>Company_A and Person_C are related because Person_C is director of Company_A<|>1))
    """.strip()
]

MOCK_LLM_ENTITY_CONFIG = {
    "type": LLMType.StaticResponse,
    "responses": MOCK_LLM_ENTITY_RESPONSES,
}

MOCK_LLM_SUMMARIZATION_RESPONSES = [
    """
    This is a MOCK response for the LLM. It is summarized!
    """.strip()
]

MOCK_LLM_SUMMARIZATION_CONFIG = {
    "type": LLMType.StaticResponse,
    "responses": MOCK_LLM_SUMMARIZATION_RESPONSES,
}


async def test_create_base_entity_graph():
    input_tables = load_input_tables([
        "workflow:create_base_text_units",
    ])

    nodes_expected = load_test_table("base_entity_nodes")
    edges_expected = load_test_table("base_relationship_edges")
    communities_expected = load_test_table("base_communities")

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
    )

    config = get_config_for_workflow(workflow_name)
    config["entity_extract"]["strategy"]["llm"] = MOCK_LLM_ENTITY_CONFIG
    config["summarize_descriptions"]["strategy"]["llm"] = MOCK_LLM_SUMMARIZATION_CONFIG

    steps = build_steps(config)

    await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context=context,
    )

    # graph construction creates transient tables for nodes, edges, and communities
    nodes_actual = await context.runtime_storage.get("base_entity_nodes")
    edges_actual = await context.runtime_storage.get("base_relationship_edges")
    communities_actual = await context.runtime_storage.get("base_communities")

    assert len(nodes_actual.columns) == len(nodes_expected.columns), (
        "Nodes dataframe columns differ"
    )

    assert len(edges_actual.columns) == len(edges_expected.columns), (
        "Edges dataframe columns differ"
    )

    assert len(communities_actual.columns) == len(communities_expected.columns), (
        "Edges dataframe columns differ"
    )

    # TODO: with the combined verb we can't force summarization
    # this is because the mock responses always result in a single description, which is returned verbatim rather than summarized
    # we need to update the mocking to provide somewhat unique graphs so a true merge happens
    # the assertion should grab a node and ensure the description matches the mock description, not the original as we are doing below

    assert nodes_actual["description"].values[0] == "Company_A is a test company"

    assert len(context.storage.keys()) == 0, "Storage should be empty"


async def test_create_base_entity_graph_with_snapshots():
    input_tables = load_input_tables([
        "workflow:create_base_text_units",
    ])

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
    )

    config = get_config_for_workflow(workflow_name)

    config["entity_extract"]["strategy"]["llm"] = MOCK_LLM_ENTITY_CONFIG
    config["summarize_descriptions"]["strategy"]["llm"] = MOCK_LLM_SUMMARIZATION_CONFIG
    config["snapshot_graphml"] = True
    config["snapshot_transient"] = True
    config["embed_graph_enabled"] = True  # need this on in order to see the snapshot

    steps = build_steps(config)

    await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context=context,
    )

    assert context.storage.keys() == [
        "graph.graphml",
        "base_entity_nodes.parquet",
        "base_relationship_edges.parquet",
        "base_communities.parquet",
    ], "Graph snapshot keys differ"


async def test_create_base_entity_graph_missing_llm_throws():
    input_tables = load_input_tables([
        "workflow:create_base_text_units",
    ])

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
    )

    config = get_config_for_workflow(workflow_name)

    config["entity_extract"]["strategy"]["llm"] = MOCK_LLM_ENTITY_CONFIG
    del config["summarize_descriptions"]["strategy"]["llm"]

    steps = build_steps(config)

    with pytest.raises(ValueError):  # noqa PT011
        await get_workflow_output(
            input_tables,
            {
                "steps": steps,
            },
            context=context,
        )
