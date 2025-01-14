# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.extract_graph import (
    extract_graph,
)
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.snapshot_graphml import snapshot_graphml
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "extract_graph"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> pd.DataFrame | None:
    """All the steps to create the base entity graph."""
    text_units = await load_table_from_storage(
        "create_base_text_units", context.storage
    )

    entity_extraction_llm_settings = config.get_language_model_config(
        config.entity_extraction.model_id
    )
    extraction_strategy = config.entity_extraction.resolved_strategy(
        config.root_dir, entity_extraction_llm_settings
    )
    extraction_num_threads = entity_extraction_llm_settings.parallelization_num_threads
    extraction_async_mode = entity_extraction_llm_settings.async_mode
    entity_types = config.entity_extraction.entity_types

    summarization_llm_settings = config.get_language_model_config(
        config.summarize_descriptions.model_id
    )
    summarization_strategy = config.summarize_descriptions.resolved_strategy(
        config.root_dir, summarization_llm_settings
    )
    summarization_num_threads = summarization_llm_settings.parallelization_num_threads

    base_entity_nodes, base_relationship_edges = await extract_graph(
        text_units=text_units,
        callbacks=callbacks,
        cache=context.cache,
        extraction_strategy=extraction_strategy,
        extraction_num_threads=extraction_num_threads,
        extraction_async_mode=extraction_async_mode,
        entity_types=entity_types,
        summarization_strategy=summarization_strategy,
        summarization_num_threads=summarization_num_threads,
    )

    await write_table_to_storage(
        base_entity_nodes, "base_entity_nodes", context.storage
    )
    await write_table_to_storage(
        base_relationship_edges, "base_relationship_edges", context.storage
    )

    if config.snapshots.graphml:
        # todo: extract graphs at each level, and add in meta like descriptions
        graph = create_graph(base_relationship_edges)
        await snapshot_graphml(
            graph,
            name="graph",
            storage=context.storage,
        )
