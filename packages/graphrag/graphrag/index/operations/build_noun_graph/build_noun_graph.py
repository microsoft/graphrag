# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Graph extraction using NLP."""

import logging
from collections import defaultdict
from itertools import combinations

import pandas as pd
from graphrag_cache import Cache
from graphrag_storage.tables.table import Table

from graphrag.graphs.edge_weights import calculate_pmi_edge_weights
from graphrag.index.operations.build_noun_graph.np_extractors.base import (
    BaseNounPhraseExtractor,
)
from graphrag.index.utils.hashing import gen_sha512_hash

logger = logging.getLogger(__name__)


async def build_noun_graph(
    text_unit_table: Table,
    text_analyzer: BaseNounPhraseExtractor,
    normalize_edge_weights: bool,
    cache: Cache,
    max_entities_per_chunk: int = 0,
    min_co_occurrence: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a noun graph from text units."""
    title_to_ids = await _extract_nodes(
        text_unit_table,
        text_analyzer,
        cache=cache,
    )

    nodes_df = pd.DataFrame(
        [
            {
                "title": title,
                "frequency": len(ids),
                "text_unit_ids": ids,
            }
            for title, ids in title_to_ids.items()
        ],
        columns=["title", "frequency", "text_unit_ids"],
    )

    edges_df = _extract_edges(
        title_to_ids,
        nodes_df=nodes_df,
        normalize_edge_weights=normalize_edge_weights,
        max_entities_per_chunk=max_entities_per_chunk,
        min_co_occurrence=min_co_occurrence,
    )
    return (nodes_df, edges_df)


async def _extract_nodes(
    text_unit_table: Table,
    text_analyzer: BaseNounPhraseExtractor,
    cache: Cache,
) -> dict[str, list[str]]:
    """Extract noun-phrase nodes from text units.

    NLP extraction is CPU-bound (spaCy/TextBlob), so threading
    provides no benefit under the GIL. We process rows
    sequentially, relying on the cache to skip repeated work.

    Returns a mapping of noun-phrase title to text-unit ids.
    """
    extraction_cache = cache.child("extract_noun_phrases")
    total = await text_unit_table.length()
    title_to_ids: dict[str, list[str]] = defaultdict(list)
    completed = 0

    async for row in text_unit_table:
        text_unit_id = row["id"]
        text = row["text"]

        attrs = {"text": text, "analyzer": str(text_analyzer)}
        key = gen_sha512_hash(attrs, attrs.keys())
        result = await extraction_cache.get(key)
        if not result:
            result = text_analyzer.extract(text)
            await extraction_cache.set(key, result)

        for phrase in result:
            title_to_ids[phrase].append(text_unit_id)

        completed += 1
        if completed % 100 == 0 or completed == total:
            logger.info(
                "extract noun phrases progress: %d/%d",
                completed,
                total,
            )

    return dict(title_to_ids)


def _extract_edges(
    title_to_ids: dict[str, list[str]],
    nodes_df: pd.DataFrame,
    normalize_edge_weights: bool = True,
    max_entities_per_chunk: int = 0,
    min_co_occurrence: int = 1,
) -> pd.DataFrame:
    """Build co-occurrence edges between noun phrases.

    Nodes that appear in the same text unit are connected.

    Two optional filters reduce O(N^2) edge explosion in
    entity-dense corpora (e.g. scientific/technical text):

    * ``max_entities_per_chunk`` – When > 0, only the K most
      globally-frequent entities per text unit are paired,
      capping edges at C(K,2) instead of C(N,2).
    * ``min_co_occurrence`` – When > 1, edges that appear in
      fewer than this many text units are discarded, removing
      coincidental co-occurrences.

    Returns edges with schema [source, target, weight, text_unit_ids].
    """
    if not title_to_ids:
        return pd.DataFrame(
            columns=["source", "target", "weight", "text_unit_ids"],
        )

    entity_freq: dict[str, int] = {
        t: len(ids) for t, ids in title_to_ids.items()
    }

    text_unit_to_titles: dict[str, list[str]] = defaultdict(list)
    for title, tu_ids in title_to_ids.items():
        for tu_id in tu_ids:
            text_unit_to_titles[tu_id].append(title)

    edge_map: dict[tuple[str, str], list[str]] = defaultdict(list)
    for tu_id, titles in text_unit_to_titles.items():
        unique_titles = sorted(set(titles))
        if len(unique_titles) < 2:
            continue
        if max_entities_per_chunk > 0 and len(unique_titles) > max_entities_per_chunk:
            unique_titles = sorted(
                unique_titles,
                key=lambda t: entity_freq.get(t, 0),
                reverse=True,
            )[:max_entities_per_chunk]
            unique_titles.sort()
        for pair in combinations(unique_titles, 2):
            edge_map[pair].append(tu_id)

    records = [
        {
            "source": src,
            "target": tgt,
            "weight": len(tu_ids),
            "text_unit_ids": tu_ids,
        }
        for (src, tgt), tu_ids in edge_map.items()
        if len(tu_ids) >= min_co_occurrence
    ]

    if len(records) < len(edge_map):
        logger.info(
            "Edge co-occurrence filter: %d -> %d edges (min_co_occurrence=%d)",
            len(edge_map),
            len(records),
            min_co_occurrence,
        )

    edges_df = pd.DataFrame(
        records,
        columns=["source", "target", "weight", "text_unit_ids"],
    )

    if normalize_edge_weights and not edges_df.empty:
        edges_df = calculate_pmi_edge_weights(nodes_df, edges_df)

    return edges_df
