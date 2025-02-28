# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.config.models.extract_graph_nlp_config import ExtractGraphNLPConfig
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.build_noun_graph.build_noun_graph import build_noun_graph
from graphrag.index.operations.build_noun_graph.np_extractors.factory import (
    create_noun_phrase_extractor,
)
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to create the base entity graph."""
    text_units = await load_table_from_storage("text_units", context.storage)

    entities, relationships = await extract_graph_nlp(
        text_units,
        context.cache,
        extraction_config=config.extract_graph_nlp,
    )

    await write_table_to_storage(entities, "entities", context.storage)
    await write_table_to_storage(relationships, "relationships", context.storage)

    return WorkflowFunctionOutput(
        result={
            "entities": entities,
            "relationships": relationships,
        }
    )


async def extract_graph_nlp(
    text_units: pd.DataFrame,
    cache: PipelineCache,
    extraction_config: ExtractGraphNLPConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the steps to create the base entity graph."""
    text_analyzer_config = extraction_config.text_analyzer
    text_analyzer = create_noun_phrase_extractor(text_analyzer_config)
    extracted_nodes, extracted_edges = await build_noun_graph(
        text_units,
        text_analyzer=text_analyzer,
        normalize_edge_weights=extraction_config.normalize_edge_weights,
        num_threads=extraction_config.concurrent_requests,
        cache=cache,
    )

    # add in any other columns required by downstream workflows
    extracted_nodes["type"] = "NOUN PHRASE"
    extracted_nodes["description"] = ""
    extracted_edges["description"] = ""

    return (extracted_nodes, extracted_edges)
