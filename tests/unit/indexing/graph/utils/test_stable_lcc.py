# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import unittest

import networkx as nx

from graphrag.index.graph.utils.stable_lcc import stable_largest_connected_component


class TestStableLCC(unittest.TestCase):
    def test_undirected_graph_run_twice_produces_same_graph(self):
        graph_in_1 = self._create_strongly_connected_graph()
        graph_out_1 = stable_largest_connected_component(graph_in_1)

        graph_in_2 = self._create_strongly_connected_graph_with_edges_flipped()
        graph_out_2 = stable_largest_connected_component(graph_in_2)

        # Make sure they're the same
        assert "".join(nx.generate_graphml(graph_out_1)) == "".join(
            nx.generate_graphml(graph_out_2)
        )

    def test_directed_graph_keeps_source_target_intact(self):
        # create the test graph as a directed graph
        graph_in = self._create_strongly_connected_graph_with_edges_flipped(
            digraph=True
        )
        graph_out = stable_largest_connected_component(graph_in.copy())

        # Make sure edges are the same and the direction is preserved
        edges_1 = [f"{edge[0]} -> {edge[1]}" for edge in graph_in.edges(data=True)]
        edges_2 = [f"{edge[0]} -> {edge[1]}" for edge in graph_out.edges(data=True)]

        assert edges_1 == edges_2

    def test_directed_graph_run_twice_produces_same_graph(self):
        # create the test graph as a directed graph
        graph_in = self._create_strongly_connected_graph_with_edges_flipped(
            digraph=True
        )
        graph_out_1 = stable_largest_connected_component(graph_in.copy())
        graph_out_2 = stable_largest_connected_component(graph_in.copy())

        # Make sure the output is identical when run multiple times
        assert "".join(nx.generate_graphml(graph_out_1)) == "".join(
            nx.generate_graphml(graph_out_2)
        )

    def _create_strongly_connected_graph(self, digraph=False):
        graph = nx.Graph() if not digraph else nx.DiGraph()
        graph.add_node("1", node_name=1)
        graph.add_node("2", node_name=2)
        graph.add_node("3", node_name=3)
        graph.add_node("4", node_name=4)
        graph.add_edge("4", "5", degree=4)
        graph.add_edge("3", "4", degree=3)
        graph.add_edge("2", "3", degree=2)
        graph.add_edge("1", "2", degree=1)
        return graph

    def _create_strongly_connected_graph_with_edges_flipped(self, digraph=False):
        graph = nx.Graph() if not digraph else nx.DiGraph()
        graph.add_node("1", node_name=1)
        graph.add_node("2", node_name=2)
        graph.add_node("3", node_name=3)
        graph.add_node("4", node_name=4)
        graph.add_edge("5", "4", degree=4)
        graph.add_edge("4", "3", degree=3)
        graph.add_edge("3", "2", degree=2)
        graph.add_edge("2", "1", degree=1)
        return graph
