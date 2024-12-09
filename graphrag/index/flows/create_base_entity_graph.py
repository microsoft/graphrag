# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any, cast
from uuid import uuid4

import networkx as nx
import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
)

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.cluster_graph import cluster_graph
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.extract_entities import extract_entities
from graphrag.index.operations.snapshot import snapshot
from graphrag.index.operations.snapshot_graphml import snapshot_graphml
from graphrag.index.operations.summarize_descriptions import (
    summarize_descriptions,
)
from graphrag.storage.pipeline_storage import PipelineStorage


async def create_base_entity_graph(
    text_units: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    runtime_storage: PipelineStorage,
    clustering_strategy: dict[str, Any],
    extraction_strategy: dict[str, Any] | None = None,
    extraction_num_threads: int = 4,
    extraction_async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    summarization_strategy: dict[str, Any] | None = None,
    summarization_num_threads: int = 4,
    snapshot_graphml_enabled: bool = False,
    snapshot_transient_enabled: bool = False,
) -> None:
    """All the steps to create the base entity graph."""
    # this returns a graph for each text unit, to be merged later
    entity_dfs, relationship_dfs = await extract_entities(
        text_units,
        callbacks,
        cache,
        text_column="text",
        id_column="id",
        strategy=extraction_strategy,
        async_mode=extraction_async_mode,
        entity_types=entity_types,
        num_threads=extraction_num_threads,
    )

    merged_entities = _merge_entities(entity_dfs)
    merged_relationships = _merge_relationships(relationship_dfs)

    entity_summaries, relationship_summaries = await summarize_descriptions(
        merged_entities,
        merged_relationships,
        callbacks,
        cache,
        strategy=summarization_strategy,
        num_threads=summarization_num_threads,
    )

    base_relationship_edges = _prep_edges(merged_relationships, relationship_summaries)

    graph = create_graph(base_relationship_edges)

    base_entity_nodes = _prep_nodes(merged_entities, entity_summaries, graph)

    communities = cluster_graph(
        graph,
        strategy=clustering_strategy,
    )

    base_communities = _prep_communities(communities)

    await runtime_storage.set("base_entity_nodes", base_entity_nodes)
    await runtime_storage.set("base_relationship_edges", base_relationship_edges)
    await runtime_storage.set("base_communities", base_communities)

    if snapshot_graphml_enabled:
        # todo: extract graphs at each level, and add in meta like descriptions
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
        await snapshot(
            base_communities,
            name="base_communities",
            storage=storage,
            formats=["parquet"],
        )


def _merge_entities(entity_dfs) -> pd.DataFrame:
    all_entities = pd.concat(entity_dfs, ignore_index=True)
    return (
        all_entities.groupby(["name", "type"], sort=False)
        .agg({"description": list, "source_id": list})
        .reset_index()
    )


def _merge_relationships(relationship_dfs) -> pd.DataFrame:
    all_relationships = pd.concat(relationship_dfs, ignore_index=False)
    return (
        all_relationships.groupby(["source", "target"], sort=False)
        .agg({"description": list, "source_id": list, "weight": "sum"})
        .reset_index()
    )


def _prep_nodes(entities, summaries, graph) -> pd.DataFrame:
    degrees_df = _compute_degree(graph)
    entities.drop(columns=["description"], inplace=True)
    nodes = (
        entities.merge(summaries, on="name", how="left")
        .merge(degrees_df, on="name")
        .drop_duplicates(subset="name")
        .rename(columns={"name": "title", "source_id": "text_unit_ids"})
    )
    nodes = nodes.loc[nodes["title"].notna()].reset_index()
    nodes["human_readable_id"] = nodes.index
    nodes["id"] = nodes["human_readable_id"].apply(lambda _x: str(uuid4()))
    return nodes


def _prep_edges(relationships, summaries) -> pd.DataFrame:
    edges = (
        relationships.drop(columns=["description"])
        .drop_duplicates(subset=["source", "target"])
        .merge(summaries, on=["source", "target"], how="left")
        .rename(columns={"source_id": "text_unit_ids"})
    )
    edges["human_readable_id"] = edges.index
    edges["id"] = edges["human_readable_id"].apply(lambda _x: str(uuid4()))
    return edges


def _prep_communities(communities) -> pd.DataFrame:
    base_communities = pd.DataFrame(
        communities, columns=cast("Any", ["level", "community", "title"])
    )
    base_communities = base_communities.explode("title")
    base_communities["community"] = base_communities["community"].astype(int)
    return base_communities


def _compute_degree(graph: nx.Graph) -> pd.DataFrame:
    return pd.DataFrame([
        {"name": node, "degree": int(degree)}
        for node, degree in graph.degree  # type: ignore
    ])
