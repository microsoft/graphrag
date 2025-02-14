# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Graph extraction using NLP."""

import math

import pandas as pd

from graphrag.cache.noop_pipeline_cache import NoopPipelineCache
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.config.enums import AsyncType
from graphrag.index.operations.build_noun_graph.np_extractors.base import (
    BaseNounPhraseExtractor,
)
from graphrag.index.run.derive_from_rows import derive_from_rows
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
    ).drop_duplicates()

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
        text_units_df.groupby("text_unit_id").agg({"title": list}).reset_index()
    )
    text_units_df["edges"] = text_units_df["title"].apply(
        lambda x: _create_relationships(x)
    )
    edge_df = text_units_df.explode("edges").loc[:, ["edges", "text_unit_id"]]

    edge_df["source"] = edge_df["edges"].apply(
        lambda x: x[0] if isinstance(x, tuple) else None
    )
    edge_df["target"] = edge_df["edges"].apply(
        lambda x: x[1] if isinstance(x, tuple) else None
    )
    edge_df = edge_df[(edge_df.source.notna()) & (edge_df.target.notna())]
    edge_df = edge_df.drop(columns=["edges"])

    # make sure source is always smaller than target
    edge_df["source"], edge_df["target"] = zip(
        *edge_df.apply(
            lambda x: (x["source"], x["target"])
            if x["source"] < x["target"]
            else (x["target"], x["source"]),
            axis=1,
        ),
        strict=False,
    )

    # group by source and target, count the number of text units and collect their ids
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
        grouped_edge_df = _calculate_pmi_edge_weights(nodes_df, grouped_edge_df)

    return grouped_edge_df


def _create_relationships(
    noun_phrases: list[str],
) -> list[tuple[str, str]]:
    """Create a (source, target) tuple pairwise for all noun phrases in a list."""
    relationships = []
    if len(noun_phrases) >= 2:
        for i in range(len(noun_phrases) - 1):
            for j in range(i + 1, len(noun_phrases)):
                relationships.extend([(noun_phrases[i], noun_phrases[j])])
    return relationships


def _calculate_pmi_edge_weights(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    node_name_col="title",
    node_freq_col="frequency",
    edge_weight_col="weight",
    edge_source_col="source",
    edge_target_col="target",
) -> pd.DataFrame:
    """
    Calculate pointwise mutual information (PMI) edge weights.

    pmi(x,y) = log2(p(x,y) / (p(x)p(y)))
    p(x,y) = edge_weight(x,y) / total_edge_weights
    p(x) = freq_occurrence(x) / total_freq_occurrences
    """
    copied_nodes_df = nodes_df[[node_name_col, node_freq_col]]

    total_edge_weights = edges_df[edge_weight_col].sum()
    total_freq_occurrences = nodes_df[node_freq_col].sum()
    copied_nodes_df["prop_occurrence"] = (
        copied_nodes_df[node_freq_col] / total_freq_occurrences
    )
    copied_nodes_df = copied_nodes_df.loc[:, [node_name_col, "prop_occurrence"]]

    edges_df["prop_weight"] = edges_df[edge_weight_col] / total_edge_weights
    edges_df = (
        edges_df.merge(
            copied_nodes_df, left_on=edge_source_col, right_on=node_name_col, how="left"
        )
        .drop(columns=[node_name_col])
        .rename(columns={"prop_occurrence": "source_prop"})
    )
    edges_df = (
        edges_df.merge(
            copied_nodes_df, left_on=edge_target_col, right_on=node_name_col, how="left"
        )
        .drop(columns=[node_name_col])
        .rename(columns={"prop_occurrence": "target_prop"})
    )
    edges_df[edge_weight_col] = edges_df.apply(
        lambda x: math.log2(x["prop_weight"] / (x["source_prop"] * x["target_prop"])),
        axis=1,
    )
    return edges_df.drop(columns=["prop_weight", "source_prop", "target_prop"])
