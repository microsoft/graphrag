import networkx as nx
import random
from typing import List, Dict, Optional, Any
from graphrag.query.structured_search.drift_search.action import DriftAction


class QueryState:
    """
    Manages the state of the query, including a graph of actions.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_action(self, action: DriftAction, metadata: Optional[Dict[str, Any]] = None):
        """
        Adds an action to the graph with optional metadata.
        """
        self.graph.add_node(action, **(metadata or {}))

    def relate_actions(self, parent: DriftAction, child: DriftAction, weight: float = 1.0):
        """
        Relates two actions in the graph.
        """
        self.graph.add_edge(parent, child, weight=weight)

    def add_all_follow_ups(self, action: DriftAction, follow_ups: List[DriftAction] | List[str], weight: float = 1.0):
        """
        Adds all follow-up actions and links them to the given action.
        """
        if len(follow_ups) == 0:
            raise ValueError("No follow-up actions to add. Please provide a list of follow-up actions.")

        for follow_up in follow_ups:
            if isinstance(follow_up, str):
                follow_up = DriftAction(query=follow_up)

            self.add_action(follow_up)
            self.relate_actions(action, follow_up, weight)

    def find_incomplete_actions(self) -> List[DriftAction]:
        """
        Finds all unanswered actions in the graph.
        """
        return [node for node in self.graph.nodes if not node.is_complete]

    def rank_incomplete_actions(self, scorer: Any | None = None) -> List[DriftAction]:
        """
        Ranks all unanswered actions in the graph if scorer available.
        """
        unanswered = self.find_incomplete_actions()
        if scorer:
            for node in unanswered:
                node.compute_score(scorer)
            return list(sorted(
                unanswered,
                key=lambda node: node.score if node.score is not None else float('-inf'),
                reverse=True
            ))
        else:  # shuffle the list if no scorer
            random.shuffle(unanswered)
            return list(unanswered)

    def serialize(self) -> Dict[str, Any]:
        """
        Serializes the graph to a dictionary, including nodes and edges.
        """
        # Create a mapping from nodes to unique IDs
        node_to_id = {node: idx for idx, node in enumerate(self.graph.nodes())}

        # Serialize nodes
        nodes = []
        for node in self.graph.nodes():
            node_data = node.serialize(include_follow_ups=False)
            node_data['id'] = node_to_id[node]
            node_attributes = self.graph.nodes[node]
            if node_attributes:
                node_data.update(node_attributes)
            nodes.append(node_data)

        # Serialize edges
        edges = []
        for u, v, edge_data in self.graph.edges(data=True):
            edge_info = {
                "source": node_to_id[u],
                "target": node_to_id[v],
                "weight": edge_data.get("weight", 1.0),
            }
            edges.append(edge_info)

        return {"nodes": nodes, "edges": edges}

    def deserialize(self, data: Dict[str, Any]):
        """
        Deserializes the dictionary back to a graph.
        """
        self.graph.clear()
        id_to_action = {}

        for node_data in data.get("nodes", []):
            node_id = node_data.pop('id')
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
