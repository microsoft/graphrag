# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from typing import Any

import pandas as pd
from graphrag_storage.tables.table import Table

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.row_transformers import (
    transform_entity_row,
    transform_relationship_row,
)
from graphrag.graphs.compute_degree import compute_degree
from graphrag.index.operations.finalize_entities import finalize_entities
from graphrag.index.operations.finalize_relationships import (
    finalize_relationships,
)
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

    async with (
        context.output_table_provider.open(
            "entities",
            transformer=transform_entity_row,
        ) as entities_table,
        context.output_table_provider.open(
            "relationships",
            transformer=transform_relationship_row,
        ) as relationships_table,
    ):
        result = await finalize_graph(
            entities_table,
            relationships_table,
        )

    if config.snapshots.graphml:
        rels = await context.output_table_provider.read_dataframe("relationships")
        await snapshot_graphml(
            rels,
            name="graph",
            storage=context.output_storage,
        )

    logger.info("Workflow completed: finalize_graph")
    return WorkflowFunctionOutput(result=result)


async def finalize_graph(
    entities_table: Table,
    relationships_table: Table,
) -> dict[str, list[dict[str, Any]]]:
    """Compute degrees and finalize entities and relationships.

    Reads all relationship rows into a DataFrame for degree
    computation, then delegates to the individual finalize operations
    for streaming row-by-row enrichment and writing.

    Args
    ----
        entities_table: Table
            Opened table for reading and writing entity rows.
        relationships_table: Table
            Opened table for reading relationships into a DataFrame
            and writing finalized relationship rows.

    Returns
    -------
        dict[str, list[dict[str, Any]]]
            Sample rows keyed by ``"entities"`` and
            ``"relationships"``, up to 5 each.
    """
    relationships = pd.DataFrame([row async for row in relationships_table])

    degree_map = _build_degree_map(relationships)

    entity_samples = await finalize_entities(entities_table, degree_map)
    relationship_samples = await finalize_relationships(relationships_table, degree_map)

    return {
        "entities": entity_samples,
        "relationships": relationship_samples,
    }


def _build_degree_map(
    relationships: pd.DataFrame,
) -> dict[str, int]:
    """Compute node degrees and return as a title-to-degree dict.

    Args
    ----
        relationships: pd.DataFrame
            Full relationships DataFrame with source/target columns.

    Returns
    -------
        dict[str, int]
            Mapping of entity title to its node degree.
    """
    degrees = compute_degree(relationships)
    return dict(zip(degrees["title"], degrees["degree"], strict=True))
