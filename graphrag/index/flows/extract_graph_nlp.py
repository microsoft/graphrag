# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from uuid import uuid4

import pandas as pd

from graphrag.config.models.extract_graph_nlp_config import ExtractGraphNLPConfig
from graphrag.config.models.prune_graph_config import PruneGraphConfig
from graphrag.index.operations.build_noun_graph.build_noun_graph import build_noun_graph
from graphrag.index.operations.build_noun_graph.np_extractors.factory import (
    create_noun_phrase_extractor,
)
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.graph_to_dataframes import graph_to_dataframes
from graphrag.index.operations.prune_graph import prune_graph


def extract_graph_nlp(
    text_units: pd.DataFrame,
    extraction_config: ExtractGraphNLPConfig,
    pruning_config: PruneGraphConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the steps to create the base entity graph."""
    text_analyzer_config = extraction_config.text_analyzer
    text_analyzer = create_noun_phrase_extractor(text_analyzer_config)
    extracted_nodes, extracted_edges = build_noun_graph(
        text_units,
        text_analyzer=text_analyzer,
        normalize_edge_weights=extraction_config.normalize_edge_weights,
    )

    # create a temporary graph to prune, then turn it back into dataframes
    graph = create_graph(extracted_edges, edge_attr=["weight"], nodes=extracted_nodes)
    pruned = prune_graph(
        graph,
        min_node_freq=pruning_config.min_node_freq,
        max_node_freq_std=pruning_config.max_node_freq_std,
        min_node_degree=pruning_config.min_node_degree,
        max_node_degree_std=pruning_config.max_node_degree_std,
        min_edge_weight_pct=pruning_config.min_edge_weight_pct,
        remove_ego_nodes=pruning_config.remove_ego_nodes,
        lcc_only=pruning_config.lcc_only,
    )

    pruned_nodes, pruned_edges = graph_to_dataframes(
        pruned, node_columns=["title"], edge_columns=["source", "target"]
    )

    # subset the full nodes and edges to only include the pruned remainders
    joined_nodes = pruned_nodes.merge(extracted_nodes, on="title", how="inner")
    joined_edges = pruned_edges.merge(
        extracted_edges, on=["source", "target"], how="inner"
    )

    # add in any other columns required by downstream workflows
    base_entity_nodes = _prep_nodes(joined_nodes)
    base_relationship_edges = _prep_edges(joined_edges)

    return (base_entity_nodes, base_relationship_edges)


def _prep_nodes(nodes) -> pd.DataFrame:
    nodes.reset_index(inplace=True)
    nodes["type"] = "NOUN PHRASE"
    nodes["description"] = ""
    nodes["human_readable_id"] = nodes.index
    nodes["id"] = nodes["human_readable_id"].apply(lambda _x: str(uuid4()))
    return nodes


def _prep_edges(edges) -> pd.DataFrame:
    edges = edges.drop_duplicates(subset=["source", "target"])
    edges.reset_index(inplace=True)
    edges["description"] = ""
    edges["human_readable_id"] = edges.index
    edges["id"] = edges["human_readable_id"].apply(lambda _x: str(uuid4()))
    return edges
