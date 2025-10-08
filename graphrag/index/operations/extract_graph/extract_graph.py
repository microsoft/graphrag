# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing entity_extract methods."""

import logging

import networkx as nx
import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.index.operations.extract_graph.graph_extractor import GraphExtractor
from graphrag.index.operations.extract_graph.typing import (
    Document,
    EntityExtractionResult,
    EntityTypes,
)
from graphrag.index.utils.derive_from_rows import derive_from_rows
from graphrag.language_model.manager import ModelManager

logger = logging.getLogger(__name__)


async def extract_graph(
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    text_column: str,
    id_column: str,
    model_config: LanguageModelConfig,
    prompt: str,
    entity_types: list[str],
    max_gleanings: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract a graph from a piece of text using a language model."""
    num_started = 0

    async def run_strategy(row):
        nonlocal num_started
        text = row[text_column]
        id = row[id_column]
        result = await run_extract_graph(
            [Document(text=text, id=id)],
            entity_types,
            cache,
            model_config,
            prompt,
            max_gleanings,
        )
        num_started += 1
        return [result.entities, result.relationships, result.graph]

    results = await derive_from_rows(
        text_units,
        run_strategy,
        callbacks,
        async_type=model_config.async_mode,
        num_threads=model_config.concurrent_requests,
        progress_msg="extract graph progress: ",
    )

    entity_dfs = []
    relationship_dfs = []
    for result in results:
        if result:
            entity_dfs.append(pd.DataFrame(result[0]))
            relationship_dfs.append(pd.DataFrame(result[1]))

    entities = _merge_entities(entity_dfs)
    relationships = _merge_relationships(relationship_dfs)

    return (entities, relationships)


async def run_extract_graph(
    docs: list[Document],
    entity_types: EntityTypes,
    cache: PipelineCache,
    model_config: LanguageModelConfig,
    prompt: str,
    max_gleanings: int,
) -> EntityExtractionResult:
    """Run the graph intelligence entity extraction strategy."""
    model = ModelManager().get_or_create_chat_model(
        name="extract_graph",
        model_type=model_config.type,
        config=model_config,
        cache=cache,
    )
    extractor = GraphExtractor(
        model=model,
        prompt=prompt,
        max_gleanings=max_gleanings,
        on_error=lambda e, s, d: logger.error(
            "Entity Extraction Error", exc_info=e, extra={"stack": s, "details": d}
        ),
    )
    text_list = [doc.text.strip() for doc in docs]

    results = await extractor(
        list(text_list),
        entity_types=entity_types,
    )

    graph = results.output
    # Map the "source_id" back to the "id" field
    for _, node in graph.nodes(data=True):  # type: ignore
        if node is not None:
            node["source_id"] = ",".join(
                docs[int(id)].id for id in node["source_id"].split(",")
            )

    for _, _, edge in graph.edges(data=True):  # type: ignore
        if edge is not None:
            edge["source_id"] = ",".join(
                docs[int(id)].id for id in edge["source_id"].split(",")
            )

    entities = [
        ({"title": item[0], **(item[1] or {})})
        for item in graph.nodes(data=True)
        if item is not None
    ]

    relationships = nx.to_pandas_edgelist(graph)

    return EntityExtractionResult(entities, relationships, graph)


def _merge_entities(entity_dfs) -> pd.DataFrame:
    all_entities = pd.concat(entity_dfs, ignore_index=True)
    return (
        all_entities.groupby(["title", "type"], sort=False)
        .agg(
            description=("description", list),
            text_unit_ids=("source_id", list),
            frequency=("source_id", "count"),
        )
        .reset_index()
    )


def _merge_relationships(relationship_dfs) -> pd.DataFrame:
    all_relationships = pd.concat(relationship_dfs, ignore_index=False)
    return (
        all_relationships.groupby(["source", "target"], sort=False)
        .agg(
            description=("description", list),
            text_unit_ids=("source_id", list),
            weight=("weight", "sum"),
        )
        .reset_index()
    )
