# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""NLP-based graph extraction workflow."""

import logging
from typing import Any

import pandas as pd
from graphrag_cache import Cache
from graphrag_storage.tables.table import Table

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.build_noun_graph.build_noun_graph import (
    build_noun_graph,
)
from graphrag.index.operations.build_noun_graph.np_extractors.base import (
    BaseNounPhraseExtractor,
)
from graphrag.index.operations.build_noun_graph.np_extractors.factory import (
    create_noun_phrase_extractor,
)
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Run the NLP graph-extraction pipeline."""
    logger.info("Workflow started: extract_graph_nlp")

    text_analyzer_config = config.extract_graph_nlp.text_analyzer
    text_analyzer = create_noun_phrase_extractor(text_analyzer_config)

    async with (
        context.output_table_provider.open(
            "text_units", truncate=False
        ) as text_units_table,
        context.output_table_provider.open("entities") as entities_table,
        context.output_table_provider.open(
            "relationships",
        ) as relationships_table,
    ):
        result = await extract_graph_nlp(
            text_units_table,
            context.cache,
            entities_table=entities_table,
            relationships_table=relationships_table,
            text_analyzer=text_analyzer,
            normalize_edge_weights=(config.extract_graph_nlp.normalize_edge_weights),
            max_entities_per_chunk=(
                config.extract_graph_nlp.max_entities_per_chunk
            ),
            min_co_occurrence=config.extract_graph_nlp.min_co_occurrence,
        )

    logger.info("Workflow completed: extract_graph_nlp")
    return WorkflowFunctionOutput(result=result)


async def extract_graph_nlp(
    text_units_table: Table,
    cache: Cache,
    entities_table: Table,
    relationships_table: Table,
    text_analyzer: BaseNounPhraseExtractor,
    normalize_edge_weights: bool,
    max_entities_per_chunk: int = 0,
    min_co_occurrence: int = 1,
) -> dict[str, list[dict[str, Any]]]:
    """Extract noun-phrase graph and stream results to output tables."""
    extracted_nodes, extracted_edges = await build_noun_graph(
        text_units_table,
        text_analyzer=text_analyzer,
        normalize_edge_weights=normalize_edge_weights,
        cache=cache,
        max_entities_per_chunk=max_entities_per_chunk,
        min_co_occurrence=min_co_occurrence,
    )

    if len(extracted_nodes) == 0:
        error_msg = (
            "NLP Graph Extraction failed. No entities detected during extraction."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    if len(extracted_edges) == 0:
        error_msg = (
            "NLP Graph Extraction failed. No relationships detected during extraction."
        )
        logger.error(error_msg)

    entity_samples = await _write_entities(
        extracted_nodes,
        entities_table,
    )
    relationship_samples = await _write_relationships(
        extracted_edges,
        relationships_table,
    )

    return {
        "entities": entity_samples,
        "relationships": relationship_samples,
    }


async def _write_entities(
    nodes_df: pd.DataFrame,
    table: Table,
) -> list[dict[str, Any]]:
    """Stream entity rows into the output table."""
    samples: list[dict[str, Any]] = []
    for row_tuple in nodes_df.itertuples(index=False):
        row = {
            "title": row_tuple.title,
            "frequency": row_tuple.frequency,
            "text_unit_ids": row_tuple.text_unit_ids,
            "type": "NOUN PHRASE",
            "description": "",
        }
        await table.write(row)
        if len(samples) < 5:
            samples.append(row)
    return samples


async def _write_relationships(
    edges_df: pd.DataFrame,
    table: Table,
) -> list[dict[str, Any]]:
    """Stream relationship rows into the output table."""
    samples: list[dict[str, Any]] = []
    for row_tuple in edges_df.itertuples(index=False):
        row = {
            "source": row_tuple.source,
            "target": row_tuple.target,
            "weight": row_tuple.weight,
            "text_unit_ids": row_tuple.text_unit_ids,
            "description": "",
        }
        await table.write(row)
        if len(samples) < 5:
            samples.append(row)
    return samples
