# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.config.models.extract_graph_nlp_config import ExtractGraphNLPConfig
from graphrag.index.operations.build_noun_graph.build_noun_graph import build_noun_graph
from graphrag.index.operations.build_noun_graph.np_extractors.factory import (
    create_noun_phrase_extractor,
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
        num_threads=extraction_config.parallelization_num_threads,
        cache=cache,
    )

    # add in any other columns required by downstream workflows
    extracted_nodes["type"] = "NOUN PHRASE"
    extracted_nodes["description"] = ""
    extracted_edges["description"] = ""

    return (extracted_nodes, extracted_edges)
