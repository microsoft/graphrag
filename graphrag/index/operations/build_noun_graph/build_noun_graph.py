# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Graph extraction using NLP."""

import math
import re
from typing import TYPE_CHECKING, cast

import nltk
import pandas as pd
from textblob import TextBlob

if TYPE_CHECKING:
    from textblob.blob import WordList


def build_noun_graph(
    text_unit_df: pd.DataFrame,
    max_word_length: int,
    normalize_edge_weights: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a noun graph from text units."""
    _download_dependencies()

    text_units = text_unit_df.loc[:, ["id", "text"]]
    nodes_df = _extract_nodes(text_units, max_word_length)
    edges_df = _extract_edges(nodes_df, normalize_edge_weights=normalize_edge_weights)

    return (nodes_df, edges_df)


def _extract_noun_phrases(
    text: str,
    max_word_length: int = 20,
) -> list[str]:
    """Extract all noun phrases from a text chunk."""
    noun_phrases = cast("WordList", TextBlob(text).noun_phrases)
    filtered_noun_phrases = set()
    for noun_phrase in noun_phrases:
        parts = [p for p in re.split(r"[\s]+", noun_phrase) if len(p) > 0]
        if len(parts) == 0:
            continue
        if (
            (len(parts) > 1 or "-" in parts[0])
            and all(re.match(r"^[a-zA-Z0-9\-]+\n?$", part) for part in parts)
            and all(len(y) < max_word_length for y in parts)
        ):
            filtered_noun_phrases.add(noun_phrase.replace("\n", "").upper())
    return list(filtered_noun_phrases)


def _extract_nodes(
    text_unit_df: pd.DataFrame,
    max_word_length: int = 20,
) -> pd.DataFrame:
    """
    Extract initial nodes and edges from text units.

    Input: text unit df with schema [id, text, document_id]
    Returns a dataframe with schema [id, title, freq, text_unit_ids].
    """
    text_unit_df["noun_phrases"] = text_unit_df["text"].apply(
        lambda x: _extract_noun_phrases(x, max_word_length)
    )

    noun_node_df = text_unit_df.explode("noun_phrases")
    noun_node_df = noun_node_df.rename(
        columns={"noun_phrases": "title"}
    ).drop_duplicates()

    # group by title, count the number of text units and collect their ids
    grouped_node_df = (
        noun_node_df.groupby("title").agg(text_unit_ids=("id", list)).reset_index()
    )
    grouped_node_df["freq"] = grouped_node_df["text_unit_ids"].apply(len)
    return grouped_node_df.loc[:, ["title", "freq", "text_unit_ids"]]


def _extract_edges(
    nodes_df: pd.DataFrame,
    normalize_edge_weights: bool = True,
) -> pd.DataFrame:
    """
    Extract edges from nodes.

    Nodes appear in the same text unit are connected.
    Input: nodes_df with schema [id, title, freq, text_unit_ids]
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
    node_freq_col="freq",
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


def _download_dependencies():
    # download corpora
    _download_if_not_exists("brown")
    _download_if_not_exists("treebank")

    # download tokenizers
    _download_if_not_exists("punkt")
    _download_if_not_exists("punkt_tab")

    # Preload the corpora to avoid lazy loading issues due to
    # race conditions when running multi-threaded jobs.
    nltk.corpus.brown.ensure_loaded()
    nltk.corpus.treebank.ensure_loaded()


def _download_if_not_exists(resource_name) -> bool:
    # look under all possible categories
    root_categories = [
        "corpora",
        "tokenizers",
        "taggers",
        "chunkers",
        "classifiers",
        "stemmers",
        "stopwords",
        "languages",
        "frequent",
        "gate",
        "models",
        "mt",
        "sentiment",
        "similarity",
    ]
    for category in root_categories:
        try:
            # if found, stop looking and avoids downloading
            nltk.find(f"{category}/{resource_name}")
            return True  # noqa: TRY300
        except LookupError:
            continue

    # is not found, download
    nltk.download(resource_name)
    return False
