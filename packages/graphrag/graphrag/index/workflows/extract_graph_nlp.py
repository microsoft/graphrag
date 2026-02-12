# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd
from graphrag_cache import Cache

from graphrag.config.enums import AsyncType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
from graphrag.index.operations.build_noun_graph.build_noun_graph import build_noun_graph
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
    """All the steps to create the base entity graph."""
    logger.info("Workflow started: extract_graph_nlp")
    reader = DataReader(context.output_table_provider)
    text_units = await reader.text_units()

    text_analyzer_config = config.extract_graph_nlp.text_analyzer
    text_analyzer = create_noun_phrase_extractor(text_analyzer_config)

    entities, relationships = await extract_graph_nlp(
        text_units,
        context.cache,
        text_analyzer=text_analyzer,
        normalize_edge_weights=config.extract_graph_nlp.normalize_edge_weights,
        num_threads=config.extract_graph_nlp.concurrent_requests,
        async_type=config.extract_graph_nlp.async_mode,
    )

    await context.output_table_provider.write_dataframe("entities", entities)
    await context.output_table_provider.write_dataframe("relationships", relationships)

    logger.info("Workflow completed: extract_graph_nlp")

    return WorkflowFunctionOutput(
        result={
            "entities": entities,
            "relationships": relationships,
        }
    )


async def extract_graph_nlp(
    text_units: pd.DataFrame,
    cache: Cache,
    text_analyzer: BaseNounPhraseExtractor,
    normalize_edge_weights: bool,
    num_threads: int,
    async_type: AsyncType,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the steps to create the base entity graph."""
    extracted_nodes, extracted_edges = await build_noun_graph(
        text_units,
        text_analyzer=text_analyzer,
        normalize_edge_weights=normalize_edge_weights,
        num_threads=num_threads,
        async_mode=async_type,
        cache=cache,
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

    # add in any other columns required by downstream workflows
    extracted_nodes["type"] = "NOUN PHRASE"
    extracted_nodes["description"] = ""
    extracted_edges["description"] = ""

    return (extracted_nodes, extracted_edges)
