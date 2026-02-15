# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.prune_graph_config import PruneGraphConfig
from graphrag.data_model.data_reader import DataReader
from graphrag.index.operations.prune_graph import prune_graph as prune_graph_operation
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to create the base entity graph."""
    logger.info("Workflow started: prune_graph")
    reader = DataReader(context.output_table_provider)
    entities = await reader.entities()
    relationships = await reader.relationships()

    pruned_entities, pruned_relationships = prune_graph(
        entities,
        relationships,
        pruning_config=config.prune_graph,
    )

    await context.output_table_provider.write_dataframe("entities", pruned_entities)
    await context.output_table_provider.write_dataframe(
        "relationships", pruned_relationships
    )

    logger.info("Workflow completed: prune_graph")
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
    pruned_entities, pruned_relationships = prune_graph_operation(
        entities,
        relationships,
        min_node_freq=pruning_config.min_node_freq,
        max_node_freq_std=pruning_config.max_node_freq_std,
        min_node_degree=pruning_config.min_node_degree,
        max_node_degree_std=pruning_config.max_node_degree_std,
        min_edge_weight_pct=pruning_config.min_edge_weight_pct,
        remove_ego_nodes=pruning_config.remove_ego_nodes,
        lcc_only=pruning_config.lcc_only,
    )

    if len(pruned_entities) == 0:
        error_msg = "Graph Pruning failed. No entities remain."
        logger.error(error_msg)
        raise ValueError(error_msg)

    if len(pruned_relationships) == 0:
        error_msg = "Graph Pruning failed. No relationships remain."
        logger.error(error_msg)
        raise ValueError(error_msg)

    return (pruned_entities, pruned_relationships)
