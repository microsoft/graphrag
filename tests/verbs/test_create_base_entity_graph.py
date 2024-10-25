# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import networkx as nx
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
    load_expected,
    load_input_tables,
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
    expected = load_expected(workflow_name)

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
    )

    config = get_config_for_workflow(workflow_name)
    config["entity_extract"]["strategy"]["llm"] = MOCK_LLM_ENTITY_CONFIG
    config["summarize_descriptions"]["strategy"]["llm"] = MOCK_LLM_SUMMARIZATION_CONFIG

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context=context,
    )

    assert len(actual.columns) == len(
        expected.columns
    ), "Graph dataframe columns differ"
    # let's parse a sample of the raw graphml
    actual_graphml_0 = actual["clustered_graph"][:1][0]
    actual_graph_0 = nx.parse_graphml(actual_graphml_0)

    assert actual_graph_0.number_of_nodes() == 3
    assert actual_graph_0.number_of_edges() == 2

    # TODO: with the combined verb we can't force summarization
    # this is because the mock responses always result in a single description, which is returned verbatim rather than summarized
    # we need to update the mocking to provide somewhat unique graphs so a true merge happens
    # the assertion should grab a node and ensure the description matches the mock description, not the original as we are doing below
    nodes = list(actual_graph_0.nodes(data=True))
    assert nodes[0][1]["description"] == "Company_A is a test company"

    assert len(context.storage.keys()) == 0, "Storage should be empty"


async def test_create_base_entity_graph_with_embeddings():
    input_tables = load_input_tables([
        "workflow:create_base_text_units",
    ])
    expected = load_expected(workflow_name)

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
    )

    config = get_config_for_workflow(workflow_name)

    config["entity_extract"]["strategy"]["llm"] = MOCK_LLM_ENTITY_CONFIG
    config["summarize_descriptions"]["strategy"]["llm"] = MOCK_LLM_SUMMARIZATION_CONFIG
    config["embed_graph_enabled"] = True

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context=context,
    )

    assert (
        len(actual.columns) == len(expected.columns) + 1
    ), "Graph dataframe missing embedding column"
    assert "embeddings" in actual.columns, "Graph dataframe missing embedding column"


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
    config["raw_entity_snapshot"] = True
    config["graphml_snapshot"] = True
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
        "raw_extracted_entities.json",
        "merged_graph.graphml",
        "summarized_graph.graphml",
        "clustered_graph.graphml",
        "embedded_graph.graphml",
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
