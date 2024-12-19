# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.extract_graph import (
    extract_graph,
)
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.snapshot import snapshot
from graphrag.index.operations.snapshot_graphml import snapshot_graphml
from graphrag.storage.pipeline_storage import PipelineStorage

workflow_name = "extract_graph"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for the entity graph.

    ## Dependencies
    * `workflow:create_base_text_units`
    """
    entity_extraction_config = config.get("entity_extract", {})
    async_mode = entity_extraction_config.get("async_mode", AsyncType.AsyncIO)
    extraction_strategy = entity_extraction_config.get("strategy")
    extraction_num_threads = entity_extraction_config.get("num_threads", 4)
    entity_types = entity_extraction_config.get("entity_types")

    summarize_descriptions_config = config.get("summarize_descriptions", {})
    summarization_strategy = summarize_descriptions_config.get("strategy")
    summarization_num_threads = summarize_descriptions_config.get("num_threads", 4)

    snapshot_graphml = config.get("snapshot_graphml", False) or False
    snapshot_transient = config.get("snapshot_transient", False) or False

    return [
        {
            "verb": workflow_name,
            "args": {
                "extraction_strategy": extraction_strategy,
                "extraction_num_threads": extraction_num_threads,
                "extraction_async_mode": async_mode,
                "entity_types": entity_types,
                "summarization_strategy": summarization_strategy,
                "summarization_num_threads": summarization_num_threads,
                "snapshot_graphml_enabled": snapshot_graphml,
                "snapshot_transient_enabled": snapshot_transient,
            },
            "input": ({"source": "workflow:create_base_text_units"}),
        },
    ]


@verb(
    name=workflow_name,
    treats_input_tables_as_immutable=True,
)
async def workflow(
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    runtime_storage: PipelineStorage,
    extraction_strategy: dict[str, Any] | None,
    extraction_num_threads: int = 4,
    extraction_async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    summarization_strategy: dict[str, Any] | None = None,
    summarization_num_threads: int = 4,
    snapshot_graphml_enabled: bool = False,
    snapshot_transient_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create the base entity graph."""
    text_units = await runtime_storage.get("base_text_units")

    base_entity_nodes, base_relationship_edges = await extract_graph(
        text_units,
        callbacks,
        cache,
        extraction_strategy=extraction_strategy,
        extraction_num_threads=extraction_num_threads,
        extraction_async_mode=extraction_async_mode,
        entity_types=entity_types,
        summarization_strategy=summarization_strategy,
        summarization_num_threads=summarization_num_threads,
    )

    await runtime_storage.set("base_entity_nodes", base_entity_nodes)
    await runtime_storage.set("base_relationship_edges", base_relationship_edges)

    if snapshot_graphml_enabled:
        # todo: extract graphs at each level, and add in meta like descriptions
        graph = create_graph(base_relationship_edges)
        await snapshot_graphml(
            graph,
            name="graph",
            storage=storage,
        )

    if snapshot_transient_enabled:
        await snapshot(
            base_entity_nodes,
            name="base_entity_nodes",
            storage=storage,
            formats=["parquet"],
        )
        await snapshot(
            base_relationship_edges,
            name="base_relationship_edges",
            storage=storage,
            formats=["parquet"],
        )

    return create_verb_result(cast("Table", pd.DataFrame()))
