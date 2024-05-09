# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import unittest

import networkx as nx

from graphrag.index.verbs.entities.extraction.strategies.graph_intelligence.run_graph_intelligence import (
    Document,
    run_extract_entities,
)
from tests.unit.indexing.verbs.helpers.mock_llm import create_mock_llm


class TestRunChain(unittest.IsolatedAsyncioTestCase):
    async def test_run_extract_entities_single_document_correct_entities_returned(self):
        results = await run_extract_entities(
            docs=[Document("test_text", "1")],
            entity_types=["person"],
            reporter=None,
            args={
                "prechunked": True,
                "max_gleanings": 0,
                "summarize_descriptions": False,
            },
            llm=create_mock_llm(
                responses=[
                    """
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
                ]
            ),
        )

        # self.assertItemsEqual isn't available yet, or I am just silly
        # so we sort the lists and compare them
        assert sorted(["TEST_ENTITY_1", "TEST_ENTITY_2", "TEST_ENTITY_3"]) == sorted([
            entity["name"] for entity in results.entities
        ])

    async def test_run_extract_entities_multiple_documents_correct_entities_returned(
        self,
    ):
        results = await run_extract_entities(
            docs=[Document("text_1", "1"), Document("text_2", "2")],
            entity_types=["person"],
            reporter=None,
            args={
                "prechunked": True,
                "max_gleanings": 0,
                "summarize_descriptions": False,
            },
            llm=create_mock_llm(
                responses=[
                    """
                    ("entity"<|>TEST_ENTITY_1<|>COMPANY<|>TEST_ENTITY_1 is a test company)
                    ##
                    ("entity"<|>TEST_ENTITY_2<|>COMPANY<|>TEST_ENTITY_2 owns TEST_ENTITY_1 and also shares an address with TEST_ENTITY_1)
                    ##
                    ("relationship"<|>TEST_ENTITY_1<|>TEST_ENTITY_2<|>TEST_ENTITY_1 and TEST_ENTITY_2 are related because TEST_ENTITY_1 is 100% owned by TEST_ENTITY_2 and the two companies also share the same address)<|>2)
                    ##
                    """.strip(),
                    """
                    ("entity"<|>TEST_ENTITY_1<|>COMPANY<|>TEST_ENTITY_1 is a test company)
                    ##
                    ("entity"<|>TEST_ENTITY_3<|>PERSON<|>TEST_ENTITY_3 is director of TEST_ENTITY_1)
                    ##
                    ("relationship"<|>TEST_ENTITY_1<|>TEST_ENTITY_3<|>TEST_ENTITY_1 and TEST_ENTITY_3 are related because TEST_ENTITY_3 is director of TEST_ENTITY_1<|>1))
                    """.strip(),
                ]
            ),
        )

        # self.assertItemsEqual isn't available yet, or I am just silly
        # so we sort the lists and compare them
        assert sorted(["TEST_ENTITY_1", "TEST_ENTITY_2", "TEST_ENTITY_3"]) == sorted([
            entity["name"] for entity in results.entities
        ])

    async def test_run_extract_entities_multiple_documents_correct_edges_returned(self):
        results = await run_extract_entities(
            docs=[Document("text_1", "1"), Document("text_2", "2")],
            entity_types=["person"],
            reporter=None,
            args={
                "prechunked": True,
                "max_gleanings": 0,
                "summarize_descriptions": False,
            },
            llm=create_mock_llm(
                responses=[
                    """
                    ("entity"<|>TEST_ENTITY_1<|>COMPANY<|>TEST_ENTITY_1 is a test company)
                    ##
                    ("entity"<|>TEST_ENTITY_2<|>COMPANY<|>TEST_ENTITY_2 owns TEST_ENTITY_1 and also shares an address with TEST_ENTITY_1)
                    ##
                    ("relationship"<|>TEST_ENTITY_1<|>TEST_ENTITY_2<|>TEST_ENTITY_1 and TEST_ENTITY_2 are related because TEST_ENTITY_1 is 100% owned by TEST_ENTITY_2 and the two companies also share the same address)<|>2)
                    ##
                    """.strip(),
                    """
                    ("entity"<|>TEST_ENTITY_1<|>COMPANY<|>TEST_ENTITY_1 is a test company)
                    ##
                    ("entity"<|>TEST_ENTITY_3<|>PERSON<|>TEST_ENTITY_3 is director of TEST_ENTITY_1)
                    ##
                    ("relationship"<|>TEST_ENTITY_1<|>TEST_ENTITY_3<|>TEST_ENTITY_1 and TEST_ENTITY_3 are related because TEST_ENTITY_3 is director of TEST_ENTITY_1<|>1))
                    """.strip(),
                ]
            ),
        )

        # self.assertItemsEqual isn't available yet, or I am just silly
        # so we sort the lists and compare them
        assert results.graphml_graph is not None, "No graphml graph returned!"
        graph = nx.parse_graphml(results.graphml_graph)  # type: ignore

        # convert to strings for more visual comparison
        edges_str = sorted([f"{edge[0]} -> {edge[1]}" for edge in graph.edges])
        assert edges_str == sorted([
            "TEST_ENTITY_1 -> TEST_ENTITY_2",
            "TEST_ENTITY_1 -> TEST_ENTITY_3",
        ])

    async def test_run_extract_entities_multiple_documents_correct_entity_source_ids_mapped(
        self,
    ):
        results = await run_extract_entities(
            docs=[Document("text_1", "1"), Document("text_2", "2")],
            entity_types=["person"],
            reporter=None,
            args={
                "prechunked": True,
                "max_gleanings": 0,
                "summarize_descriptions": False,
            },
            llm=create_mock_llm(
                responses=[
                    """
                    ("entity"<|>TEST_ENTITY_1<|>COMPANY<|>TEST_ENTITY_1 is a test company)
                    ##
                    ("entity"<|>TEST_ENTITY_2<|>COMPANY<|>TEST_ENTITY_2 owns TEST_ENTITY_1 and also shares an address with TEST_ENTITY_1)
                    ##
                    ("relationship"<|>TEST_ENTITY_1<|>TEST_ENTITY_2<|>TEST_ENTITY_1 and TEST_ENTITY_2 are related because TEST_ENTITY_1 is 100% owned by TEST_ENTITY_2 and the two companies also share the same address)<|>2)
                    ##
                    """.strip(),
                    """
                    ("entity"<|>TEST_ENTITY_1<|>COMPANY<|>TEST_ENTITY_1 is a test company)
                    ##
                    ("entity"<|>TEST_ENTITY_3<|>PERSON<|>TEST_ENTITY_3 is director of TEST_ENTITY_1)
                    ##
                    ("relationship"<|>TEST_ENTITY_1<|>TEST_ENTITY_3<|>TEST_ENTITY_1 and TEST_ENTITY_3 are related because TEST_ENTITY_3 is director of TEST_ENTITY_1<|>1))
                    """.strip(),
                ]
            ),
        )

        assert results.graphml_graph is not None, "No graphml graph returned!"
        graph = nx.parse_graphml(results.graphml_graph)  # type: ignore

        # TODO: The edges might come back in any order, but we're assuming they're coming
        # back in the order that we passed in the docs, that might not be true
        assert (
            graph.nodes["TEST_ENTITY_3"].get("source_id") == "2"
        )  # TEST_ENTITY_3 should be in just 2
        assert (
            graph.nodes["TEST_ENTITY_2"].get("source_id") == "1"
        )  # TEST_ENTITY_2 should be in just 1
        assert sorted(
            graph.nodes["TEST_ENTITY_1"].get("source_id").split(",")
        ) == sorted(["1", "2"])  # TEST_ENTITY_1 should be 1 and 2

    async def test_run_extract_entities_multiple_documents_correct_edge_source_ids_mapped(
        self,
    ):
        results = await run_extract_entities(
            docs=[Document("text_1", "1"), Document("text_2", "2")],
            entity_types=["person"],
            reporter=None,
            args={
                "prechunked": True,
                "max_gleanings": 0,
                "summarize_descriptions": False,
            },
            llm=create_mock_llm(
                responses=[
                    """
                    ("entity"<|>TEST_ENTITY_1<|>COMPANY<|>TEST_ENTITY_1 is a test company)
                    ##
                    ("entity"<|>TEST_ENTITY_2<|>COMPANY<|>TEST_ENTITY_2 owns TEST_ENTITY_1 and also shares an address with TEST_ENTITY_1)
                    ##
                    ("relationship"<|>TEST_ENTITY_1<|>TEST_ENTITY_2<|>TEST_ENTITY_1 and TEST_ENTITY_2 are related because TEST_ENTITY_1 is 100% owned by TEST_ENTITY_2 and the two companies also share the same address)<|>2)
                    ##
                    """.strip(),
                    """
                    ("entity"<|>TEST_ENTITY_1<|>COMPANY<|>TEST_ENTITY_1 is a test company)
                    ##
                    ("entity"<|>TEST_ENTITY_3<|>PERSON<|>TEST_ENTITY_3 is director of TEST_ENTITY_1)
                    ##
                    ("relationship"<|>TEST_ENTITY_1<|>TEST_ENTITY_3<|>TEST_ENTITY_1 and TEST_ENTITY_3 are related because TEST_ENTITY_3 is director of TEST_ENTITY_1<|>1))
                    """.strip(),
                ]
            ),
        )

        assert results.graphml_graph is not None, "No graphml graph returned!"
        graph = nx.parse_graphml(results.graphml_graph)  # type: ignore
        edges = list(graph.edges(data=True))

        # should only have 2 edges
        assert len(edges) == 2

        # Sort by source_id for consistent ordering
        edge_source_ids = sorted([edge[2].get("source_id", "") for edge in edges])  # type: ignore
        assert edge_source_ids[0].split(",") == ["1"]  # type: ignore
        assert edge_source_ids[1].split(",") == ["2"]  # type: ignore
