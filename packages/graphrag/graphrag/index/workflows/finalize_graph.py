# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.finalize_entities import finalize_entities
from graphrag.index.operations.finalize_relationships import finalize_relationships
from graphrag.index.operations.snapshot_graphml import snapshot_graphml
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to create the base entity graph."""
    logger.info("Workflow started: finalize_graph")
    reader = DataReader(context.output_table_provider)
    entities = await reader.entities()
    relationships = await reader.relationships()

    final_entities, final_relationships = finalize_graph(
        entities,
        relationships,
    )

    await context.output_table_provider.write_dataframe("entities", final_entities)
    await context.output_table_provider.write_dataframe(
        "relationships", final_relationships
    )

    if config.snapshots.graphml:
        graph = create_graph(final_relationships, edge_attr=["weight"])

        await snapshot_graphml(
            graph,
            name="graph",
            storage=context.output_storage,
        )

    logger.info("Workflow completed: finalize_graph")
    return WorkflowFunctionOutput(
        result={
            "entities": entities,
            "relationships": relationships,
        }
    )


def finalize_graph(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the steps to finalize the entity and relationship formats."""
    final_entities = finalize_entities(entities, relationships)
    final_relationships = finalize_relationships(relationships)
    return (final_entities, final_relationships)
