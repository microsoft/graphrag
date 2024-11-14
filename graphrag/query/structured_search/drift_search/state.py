# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Manage the state of the DRIFT query, including a graph of actions."""

import logging
import random
from collections.abc import Callable
from typing import Any

import networkx as nx

from graphrag.query.structured_search.drift_search.action import DriftAction

log = logging.getLogger(__name__)


class QueryState:
    """Manage the state of the query, including a graph of actions."""

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_action(self, action: DriftAction, metadata: dict[str, Any] | None = None):
        """Add an action to the graph with optional metadata."""
        self.graph.add_node(action, **(metadata or {}))

    def relate_actions(
        self, parent: DriftAction, child: DriftAction, weight: float = 1.0
    ):
        """Relate two actions in the graph."""
        self.graph.add_edge(parent, child, weight=weight)

    def add_all_follow_ups(
        self,
        action: DriftAction,
        follow_ups: list[DriftAction] | list[str],
        weight: float = 1.0,
    ):
        """Add all follow-up actions and links them to the given action."""
        if len(follow_ups) == 0:
            log.warning("No follow-up actions for action: %s", action.query)

        for follow_up in follow_ups:
            if isinstance(follow_up, str):
                follow_up = DriftAction(query=follow_up)
            elif not isinstance(follow_up, DriftAction):
                log.warning(
                    "Follow-up action is not a string, found type: %s", type(follow_up)
                )

            self.add_action(follow_up)
            self.relate_actions(action, follow_up, weight)

    def find_incomplete_actions(self) -> list[DriftAction]:
        """Find all unanswered actions in the graph."""
        return [node for node in self.graph.nodes if not node.is_complete]

    def rank_incomplete_actions(
        self, scorer: Callable[[DriftAction], float] | None = None
    ) -> list[DriftAction]:
        """Rank all unanswered actions in the graph if scorer available."""
        unanswered = self.find_incomplete_actions()
        if scorer:
            for node in unanswered:
                node.compute_score(scorer)
            return sorted(
                unanswered,
                key=lambda node: (
                    node.score if node.score is not None else float("-inf")
                ),
                reverse=True,
            )

        # shuffle the list if no scorer
        random.shuffle(unanswered)
        return list(unanswered)

    def serialize(
        self, include_context: bool = True
    ) -> dict[str, Any] | tuple[dict[str, Any], dict[str, Any], str]:
        """Serialize the graph to a dictionary, including nodes and edges."""
        # Create a mapping from nodes to unique IDs
        node_to_id = {node: idx for idx, node in enumerate(self.graph.nodes())}

        # Serialize nodes
        nodes: list[dict[str, Any]] = [
            {
                **node.serialize(include_follow_ups=False),
                "id": node_to_id[node],
                **self.graph.nodes[node],
            }
            for node in self.graph.nodes()
        ]

        # Serialize edges
        edges: list[dict[str, Any]] = [
            {
                "source": node_to_id[u],
                "target": node_to_id[v],
                "weight": edge_data.get("weight", 1.0),
            }
            for u, v, edge_data in self.graph.edges(data=True)
        ]

        if include_context:
            context_data = {
                node["query"]: node["metadata"]["context_data"]
                for node in nodes
                if node["metadata"].get("context_data") and node.get("query")
            }

            context_text = str(context_data)

            return {"nodes": nodes, "edges": edges}, context_data, context_text

        return {"nodes": nodes, "edges": edges}

    def deserialize(self, data: dict[str, Any]):
        """Deserialize the dictionary back to a graph."""
        self.graph.clear()
        id_to_action = {}

        for node_data in data.get("nodes", []):
            node_id = node_data.pop("id")
            action = DriftAction.deserialize(node_data)
            self.add_action(action)
            id_to_action[node_id] = action

        for edge_data in data.get("edges", []):
            source_id = edge_data["source"]
            target_id = edge_data["target"]
            weight = edge_data.get("weight", 1.0)
            source_action = id_to_action.get(source_id)
            target_action = id_to_action.get(target_id)
            if source_action and target_action:
                self.relate_actions(source_action, target_action, weight)

    def action_token_ct(self) -> dict[str, int]:
        """Return the token count of the action."""
        llm_calls, prompt_tokens, output_tokens = 0, 0, 0
        for action in self.graph.nodes:
            llm_calls += action.metadata["llm_calls"]
            prompt_tokens += action.metadata["prompt_tokens"]
            output_tokens += action.metadata["output_tokens"]
        return {
            "llm_calls": llm_calls,
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
        }
