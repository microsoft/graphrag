# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.extract_graph import (
    extract_graph,
)
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.snapshot import snapshot
from graphrag.index.operations.snapshot_graphml import snapshot_graphml

workflow_name = "extract_graph"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to create the base entity graph."""
    text_units = await context.runtime_storage.get("create_base_text_units")

    extraction_strategy = config.entity_extraction.resolved_strategy(
        config.root_dir, config.encoding_model
    )
    extraction_num_threads = config.entity_extraction.parallelization.num_threads
    extraction_async_mode = config.entity_extraction.async_mode
    entity_types = config.entity_extraction.entity_types

    summarization_strategy = config.summarize_descriptions.resolved_strategy(
        config.root_dir,
    )
    summarization_num_threads = (
        config.summarize_descriptions.parallelization.num_threads
    )

    base_entity_nodes, base_relationship_edges = await extract_graph(
        text_units,
        callbacks,
        context.cache,
        extraction_strategy=extraction_strategy,
        extraction_num_threads=extraction_num_threads,
        extraction_async_mode=extraction_async_mode,
        entity_types=entity_types,
        summarization_strategy=summarization_strategy,
        summarization_num_threads=summarization_num_threads,
    )

    await context.runtime_storage.set("base_entity_nodes", base_entity_nodes)
    await context.runtime_storage.set(
        "base_relationship_edges", base_relationship_edges
    )

    if config.snapshots.graphml:
        # todo: extract graphs at each level, and add in meta like descriptions
        graph = create_graph(base_relationship_edges)
        await snapshot_graphml(
            graph,
            name="graph",
            storage=context.storage,
        )

    if config.snapshots.transient:
        await snapshot(
            base_entity_nodes,
            name="base_entity_nodes",
            storage=context.storage,
            formats=["parquet"],
        )
        await snapshot(
            base_relationship_edges,
            name="base_relationship_edges",
            storage=context.storage,
            formats=["parquet"],
        )
