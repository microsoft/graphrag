# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Graph extraction using NLP."""

import asyncio
import logging
from collections import defaultdict
from itertools import combinations

import pandas as pd
from graphrag_cache import Cache
from graphrag_storage.tables.table import Table

from graphrag.config.enums import AsyncType
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
    num_threads: int,
    async_mode: AsyncType,
    cache: Cache,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a noun graph from text units."""
    title_to_ids = await _extract_nodes(
        text_unit_table,
        text_analyzer,
        num_threads=num_threads,
        async_mode=async_mode,
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
    )
    return (nodes_df, edges_df)


async def _extract_nodes(
    text_unit_table: Table,
    text_analyzer: BaseNounPhraseExtractor,
    num_threads: int,
    async_mode: AsyncType,
    cache: Cache,
) -> dict[str, list[str]]:
    """Extract noun-phrase nodes from text units.

    Returns a mapping of noun-phrase title to text-unit ids.
    """
    extraction_cache = cache.child("extract_noun_phrases")
    semaphore = asyncio.Semaphore(num_threads)
    use_threads = async_mode == AsyncType.Threaded

    async def _extract_one(
        text_unit_id: str,
        text: str,
    ) -> tuple[str, list[str]]:
        """Return ``(text_unit_id, noun_phrases)`` for one row."""
        async with semaphore:
            attrs = {"text": text, "analyzer": str(text_analyzer)}
            key = gen_sha512_hash(attrs, attrs.keys())
            result = await extraction_cache.get(key)
            if not result:
                if use_threads:
                    result = await asyncio.to_thread(
                        text_analyzer.extract,
                        text,
                    )
                else:
                    result = text_analyzer.extract(text)
                await extraction_cache.set(key, result)
            return (text_unit_id, result)

    total = await text_unit_table.length()
    title_to_ids: dict[str, list[str]] = defaultdict(list)
    completed = 0
    chunk_size = num_threads * 4
    chunk: list[asyncio.Task[tuple[str, list[str]]]] = []

    async def _drain(
        tasks: list[asyncio.Task[tuple[str, list[str]]]],
    ) -> None:
        """Await every task in the chunk and accumulate results."""
        nonlocal completed
        for coro in asyncio.as_completed(tasks):
            text_unit_id, noun_phrases = await coro
            completed += 1
            if completed % 100 == 0 or completed == total:
                logger.info(
                    "extract noun phrases progress: %d/%d",
                    completed,
                    total,
                )
            for phrase in noun_phrases:
                title_to_ids[phrase].append(text_unit_id)

    async for row in text_unit_table:
        chunk.append(
            asyncio.create_task(
                _extract_one(row["id"], row["text"]),
            ),
        )
        if len(chunk) >= chunk_size:
            await _drain(chunk)
            chunk.clear()

    if chunk:
        await _drain(chunk)

    return dict(title_to_ids)


def _extract_edges(
    title_to_ids: dict[str, list[str]],
    nodes_df: pd.DataFrame,
    normalize_edge_weights: bool = True,
) -> pd.DataFrame:
    """Build co-occurrence edges between noun phrases.

    Nodes that appear in the same text unit are connected.
    Returns edges with schema [source, target, weight, text_unit_ids].
    """
    if not title_to_ids:
        return pd.DataFrame(
            columns=["source", "target", "weight", "text_unit_ids"],
        )

    text_unit_to_titles: dict[str, list[str]] = defaultdict(list)
    for title, tu_ids in title_to_ids.items():
        for tu_id in tu_ids:
            text_unit_to_titles[tu_id].append(title)

    edge_map: dict[tuple[str, str], list[str]] = defaultdict(list)
    for tu_id, titles in text_unit_to_titles.items():
        if len(titles) < 2:
            continue
        for pair in combinations(sorted(set(titles)), 2):
            edge_map[pair].append(tu_id)

    records = [
        {
            "source": src,
            "target": tgt,
            "weight": len(tu_ids),
            "text_unit_ids": tu_ids,
        }
        for (src, tgt), tu_ids in edge_map.items()
    ]
    edges_df = pd.DataFrame(
        records,
        columns=["source", "target", "weight", "text_unit_ids"],
    )

    if normalize_edge_weights and not edges_df.empty:
        edges_df = calculate_pmi_edge_weights(nodes_df, edges_df)

    return edges_df
