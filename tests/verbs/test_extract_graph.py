# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.enums import LLMType
from graphrag.index.workflows.extract_graph import (
    run_workflow,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    create_test_context,
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

MOCK_LLM_SUMMARIZATION_RESPONSES = [
    """
    This is a MOCK response for the LLM. It is summarized!
    """.strip()
]


async def test_extract_graph():
    nodes_expected = load_test_table("base_entity_nodes")
    edges_expected = load_test_table("base_relationship_edges")

    context = await create_test_context(
        storage=["create_base_text_units"],
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    claim_extraction_llm_settings = config.get_language_model_config(
        config.entity_extraction.model_id
    ).model_dump()
    claim_extraction_llm_settings["type"] = LLMType.StaticResponse
    claim_extraction_llm_settings["responses"] = MOCK_LLM_ENTITY_RESPONSES
    config.entity_extraction.strategy = {
        "type": "graph_intelligence",
        "llm": claim_extraction_llm_settings,
    }
    summarize_llm_settings = config.get_language_model_config(
        config.summarize_descriptions.model_id
    ).model_dump()
    summarize_llm_settings["type"] = LLMType.StaticResponse
    summarize_llm_settings["responses"] = MOCK_LLM_SUMMARIZATION_RESPONSES
    config.summarize_descriptions.strategy = {
        "type": "graph_intelligence",
        "llm": summarize_llm_settings,
    }

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    # graph construction creates transient tables for nodes, edges, and communities
    nodes_actual = await load_table_from_storage("base_entity_nodes", context.storage)
    edges_actual = await load_table_from_storage(
        "base_relationship_edges", context.storage
    )

    assert len(nodes_actual.columns) == len(nodes_expected.columns), (
        "Nodes dataframe columns differ"
    )

    assert len(edges_actual.columns) == len(edges_expected.columns), (
        "Edges dataframe columns differ"
    )

    # TODO: with the combined verb we can't force summarization
    # this is because the mock responses always result in a single description, which is returned verbatim rather than summarized
    # we need to update the mocking to provide somewhat unique graphs so a true merge happens
    # the assertion should grab a node and ensure the description matches the mock description, not the original as we are doing below
    assert nodes_actual["description"].to_numpy()[0] == "Company_A is a test company"
