# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.prune_graph_config import PruneGraphConfig
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.graph_to_dataframes import graph_to_dataframes
from graphrag.index.operations.prune_graph import prune_graph as prune_graph_operation
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to create the base entity graph."""
    entities = await load_table_from_storage("entities", context.storage)
    relationships = await load_table_from_storage("relationships", context.storage)

    pruned_entities, pruned_relationships = prune_graph(
        entities,
        relationships,
        pruning_config=config.prune_graph,
    )

    await write_table_to_storage(pruned_entities, "entities", context.storage)
    await write_table_to_storage(pruned_relationships, "relationships", context.storage)

    return WorkflowFunctionOutput(
        result={
            "entities": pruned_entities,
            "relationships": pruned_relationships,
        }
    )


def prune_graph(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
    pruning_config: PruneGraphConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prune a full graph based on graph statistics."""
    # create a temporary graph to prune, then turn it back into dataframes
    graph = create_graph(relationships, edge_attr=["weight"], nodes=entities)
    pruned = prune_graph_operation(
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
    subset_entities = pruned_nodes.merge(entities, on="title", how="inner")
    subset_relationships = pruned_edges.merge(
        relationships, on=["source", "target"], how="inner"
    )

    return (subset_entities, subset_relationships)
