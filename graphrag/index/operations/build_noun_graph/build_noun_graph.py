# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Graph extraction using NLP."""

from itertools import combinations

import numpy as np
import pandas as pd

from graphrag.cache.noop_pipeline_cache import NoopPipelineCache
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.config.enums import AsyncType
from graphrag.index.operations.build_noun_graph.np_extractors.base import (
    BaseNounPhraseExtractor,
)
from graphrag.index.utils.derive_from_rows import derive_from_rows
from graphrag.index.utils.graphs import calculate_pmi_edge_weights
from graphrag.index.utils.hashing import gen_sha512_hash


async def build_noun_graph(
    text_unit_df: pd.DataFrame,
    text_analyzer: BaseNounPhraseExtractor,
    normalize_edge_weights: bool,
    num_threads: int = 4,
    cache: PipelineCache | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a noun graph from text units."""
    text_units = text_unit_df.loc[:, ["id", "text"]]
    nodes_df = await _extract_nodes(
        text_units, text_analyzer, num_threads=num_threads, cache=cache
    )
    edges_df = _extract_edges(nodes_df, normalize_edge_weights=normalize_edge_weights)
    return (nodes_df, edges_df)


async def _extract_nodes(
    text_unit_df: pd.DataFrame,
    text_analyzer: BaseNounPhraseExtractor,
    num_threads: int = 4,
    cache: PipelineCache | None = None,
) -> pd.DataFrame:
    """
    Extract initial nodes and edges from text units.

    Input: text unit df with schema [id, text, document_id]
    Returns a dataframe with schema [id, title, frequency, text_unit_ids].
    """
    cache = cache or NoopPipelineCache()
    cache = cache.child("extract_noun_phrases")

    async def extract(row):
        text = row["text"]
        attrs = {"text": text, "analyzer": str(text_analyzer)}
        key = gen_sha512_hash(attrs, attrs.keys())
        result = await cache.get(key)
        if not result:
            result = text_analyzer.extract(text)
            await cache.set(key, result)
        return result

    text_unit_df["noun_phrases"] = await derive_from_rows(
        text_unit_df,
        extract,
        num_threads=num_threads,
        async_type=AsyncType.Threaded,
    )

    noun_node_df = text_unit_df.explode("noun_phrases")
    noun_node_df = noun_node_df.rename(
        columns={"noun_phrases": "title", "id": "text_unit_id"}
    )

    # group by title and count the number of text units
    grouped_node_df = (
        noun_node_df.groupby("title").agg({"text_unit_id": list}).reset_index()
    )
    grouped_node_df = grouped_node_df.rename(columns={"text_unit_id": "text_unit_ids"})
    grouped_node_df["frequency"] = grouped_node_df["text_unit_ids"].apply(len)
    grouped_node_df = grouped_node_df[["title", "frequency", "text_unit_ids"]]
    return grouped_node_df.loc[:, ["title", "frequency", "text_unit_ids"]]


def _extract_edges(
    nodes_df: pd.DataFrame,
    normalize_edge_weights: bool = True,
) -> pd.DataFrame:
    """
    Extract edges from nodes.

    Nodes appear in the same text unit are connected.
    Input: nodes_df with schema [id, title, frequency, text_unit_ids]
    Returns: edges_df with schema [source, target, weight, text_unit_ids]
    """
    text_units_df = nodes_df.explode("text_unit_ids")
    text_units_df = text_units_df.rename(columns={"text_unit_ids": "text_unit_id"})

    text_units_df = (
        text_units_df.groupby("text_unit_id")
        .agg({"title": lambda x: list(x) if len(x) > 1 else np.nan})
        .reset_index()
    )
    text_units_df = text_units_df.dropna()
    titles = text_units_df["title"].tolist()
    all_edges: list[list[tuple[str, str]]] = [list(combinations(t, 2)) for t in titles]

    text_units_df = text_units_df.assign(edges=all_edges)  # type: ignore
    edge_df = text_units_df.explode("edges")[["edges", "text_unit_id"]]

    edge_df[["source", "target"]] = edge_df.loc[:, "edges"].to_list()
    edge_df["min_source"] = edge_df[["source", "target"]].min(axis=1)
    edge_df["max_target"] = edge_df[["source", "target"]].max(axis=1)
    edge_df = edge_df.drop(columns=["source", "target"]).rename(
        columns={"min_source": "source", "max_target": "target"}  # type: ignore
    )

    edge_df = edge_df[(edge_df.source.notna()) & (edge_df.target.notna())]
    edge_df = edge_df.drop(columns=["edges"])
    # group by source and target, count the number of text units
    grouped_edge_df = (
        edge_df.groupby(["source", "target"]).agg({"text_unit_id": list}).reset_index()
    )
    grouped_edge_df = grouped_edge_df.rename(columns={"text_unit_id": "text_unit_ids"})
    grouped_edge_df["weight"] = grouped_edge_df["text_unit_ids"].apply(len)
    grouped_edge_df = grouped_edge_df.loc[
        :, ["source", "target", "weight", "text_unit_ids"]
    ]
    if normalize_edge_weights:
        # use PMI weight instead of raw weight
        grouped_edge_df = calculate_pmi_edge_weights(nodes_df, grouped_edge_df)

    return grouped_edge_df
