# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM-based entity resolution operation.

Identifies entities with different surface forms that refer to the same
real-world entity (e.g. "Ahab" and "Captain Ahab") and unifies their titles.
"""

import asyncio
import logging
from typing import TYPE_CHECKING

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.logger.progress import progress_ticker

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion

logger = logging.getLogger(__name__)


async def resolve_entities(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    model: "LLMCompletion",
    prompt: str,
    batch_size: int,
    num_threads: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Identify and merge duplicate entities with different surface forms.

    Sends entity names in batches to the LLM, parses the response to build
    a rename mapping, then applies it to both entity titles and relationship
    source/target columns.

    Parameters
    ----------
    entities : pd.DataFrame
        Entity DataFrame with at least a "title" column.
    relationships : pd.DataFrame
        Relationship DataFrame with "source" and "target" columns.
    callbacks : WorkflowCallbacks
        Progress callbacks.
    model : LLMCompletion
        The LLM completion model to use.
    prompt : str
        The entity resolution prompt template (must contain {entity_list}).
    batch_size : int
        Maximum number of entity names per LLM batch.
    num_threads : int
        Concurrency limit for LLM calls.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        Updated (entities, relationships) with unified titles.
    """
    if "title" not in entities.columns:
        return entities, relationships

    titles = entities["title"].dropna().unique().tolist()
    if len(titles) < 2:
        return entities, relationships

    logger.info(
        "Running LLM entity resolution on %d unique entity names...", len(titles)
    )

    # Build batches
    batches = [
        titles[i : i + batch_size] for i in range(0, len(titles), batch_size)
    ]

    ticker = progress_ticker(
        callbacks.progress,
        len(batches),
        description="Entity resolution batch progress: ",
    )

    semaphore = asyncio.Semaphore(num_threads)
    rename_map: dict[str, str] = {}  # alias → canonical

    async def process_batch(batch: list[str], batch_idx: int) -> None:
        entity_list = "\n".join(f"{i+1}. {name}" for i, name in enumerate(batch))
        formatted_prompt = prompt.format(entity_list=entity_list)

        async with semaphore:
            try:
                response = await model(formatted_prompt)
                raw = (response or "").strip()
            except Exception:
                logger.warning(
                    "Entity resolution LLM call failed for batch %d, skipping",
                    batch_idx + 1,
                )
                ticker(1)
                return

        if "NO_DUPLICATES" in raw:
            logger.info("  Batch %d: no duplicates found", batch_idx + 1)
            ticker(1)
            return

        # Parse response lines like "3, 17" or "5, 12, 28"
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("Where"):
                continue
            parts = [p.strip() for p in line.split(",")]
            indices: list[int] = []
            for p in parts:
                digits = "".join(c for c in p if c.isdigit())
                if digits:
                    idx = int(digits) - 1  # 1-indexed → 0-indexed
                    if 0 <= idx < len(batch):
                        indices.append(idx)
            if len(indices) >= 2:
                canonical = batch[indices[0]]
                for alias_idx in indices[1:]:
                    alias = batch[alias_idx]
                    rename_map[alias] = canonical
                    logger.info(
                        "  Entity resolution: '%s' → '%s'", alias, canonical
                    )

        ticker(1)

    futures = [process_batch(batch, i) for i, batch in enumerate(batches)]
    await asyncio.gather(*futures)

    if not rename_map:
        logger.info("Entity resolution complete: no duplicates found")
        return entities, relationships

    logger.info("Entity resolution: merging %d duplicate names", len(rename_map))

    # Apply renames to entity titles
    entities = entities.copy()
    entities["title"] = entities["title"].map(lambda t: rename_map.get(t, t))

    # Apply renames to relationship source/target
    if not relationships.empty:
        relationships = relationships.copy()
        if "source" in relationships.columns:
            relationships["source"] = relationships["source"].map(
                lambda s: rename_map.get(s, s)
            )
        if "target" in relationships.columns:
            relationships["target"] = relationships["target"].map(
                lambda t: rename_map.get(t, t)
            )

    return entities, relationships
