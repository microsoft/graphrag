# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import unittest

from graphrag.index.operations.extract_graph.extract_graph import _run_extract_graph
from graphrag.prompts.index.extract_graph import GRAPH_EXTRACTION_PROMPT
from graphrag_llm.completion import create_completion
from graphrag_llm.config import LLMProviderType, ModelConfig

SIMPLE_EXTRACTION_RESPONSE = """
("entity"<|>TEST_ENTITY_1<|>COMPANY<|>TEST_ENTITY_1 is a test company)
##
("entity"<|>TEST_ENTITY_2<|>COMPANY<|>TEST_ENTITY_2 owns TEST_ENTITY_1 and also shares an address with TEST_ENTITY_1)
##
("entity"<|>TEST_ENTITY_3<|>PERSON<|>TEST_ENTITY_3 is director of TEST_ENTITY_1)
##
("relationship"<|>TEST_ENTITY_1<|>TEST_ENTITY_2<|>TEST_ENTITY_1 and TEST_ENTITY_2 are related because TEST_ENTITY_1 is 100% owned by TEST_ENTITY_2 and the two companies also share the same address)<|>2)
##
("relationship"<|>TEST_ENTITY_1<|>TEST_ENTITY_3<|>TEST_ENTITY_1 and TEST_ENTITY_3 are related because TEST_ENTITY_3 is director of TEST_ENTITY_1<|>1))
""".strip()


model = create_completion(
    ModelConfig(
        type=LLMProviderType.MockLLM,
        model_provider="openai",
        model="gpt-4o",
        mock_responses=[SIMPLE_EXTRACTION_RESPONSE],
    )
)


class TestRunChain(unittest.IsolatedAsyncioTestCase):
    async def test_run_extract_graph_single_document_correct_entities_returned(self):
        entities_df, _ = await _run_extract_graph(
            text="test_text",
            source_id="1",
            entity_types=["person"],
            max_gleanings=0,
            model=model,
            prompt=GRAPH_EXTRACTION_PROMPT,
        )

        assert sorted(["TEST_ENTITY_1", "TEST_ENTITY_2", "TEST_ENTITY_3"]) == sorted(
            entities_df["title"].tolist()
        )

    async def test_run_extract_graph_single_document_correct_edges_returned(self):
        _, relationships_df = await _run_extract_graph(
            text="test_text",
            source_id="1",
            entity_types=["person"],
            max_gleanings=0,
            model=model,
            prompt=GRAPH_EXTRACTION_PROMPT,
        )

        edges = relationships_df.to_dict("records")
        assert len(edges) == 2

        relationship_pairs = {(edge["source"], edge["target"]) for edge in edges}
        assert relationship_pairs == {
            ("TEST_ENTITY_1", "TEST_ENTITY_2"),
            ("TEST_ENTITY_1", "TEST_ENTITY_3"),
        }

    async def test_run_extract_graph_single_document_source_ids_mapped(self):
        entities_df, relationships_df = await _run_extract_graph(
            text="test_text",
            source_id="1",
            entity_types=["person"],
            max_gleanings=0,
            model=model,
            prompt=GRAPH_EXTRACTION_PROMPT,
        )

        assert all(source_id == "1" for source_id in entities_df["source_id"])

        assert all(source_id == "1" for source_id in relationships_df["source_id"])
