# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM-based entity resolution operation.

Identifies entities with different surface forms that refer to the same
real-world entity (e.g. "Ahab" and "Captain Ahab") and unifies their titles.
"""

import logging
from typing import TYPE_CHECKING

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion

logger = logging.getLogger(__name__)


async def resolve_entities(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    model: "LLMCompletion",
    prompt: str,
    num_threads: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Identify and merge duplicate entities with different surface forms.

    Sends all unique entity titles to the LLM in a single call, parses the
    response to build a rename mapping, then applies it to entity titles and
    relationship source/target columns.  Each canonical entity receives an
    ``alternative_names`` column listing all of its aliases.

    Parameters
    ----------
    entities : pd.DataFrame
        Entity DataFrame with at least a ``title`` column.
    relationships : pd.DataFrame
        Relationship DataFrame with ``source`` and ``target`` columns.
    callbacks : WorkflowCallbacks
        Progress callbacks.
    model : LLMCompletion
        The LLM completion model to use.
    prompt : str
        The entity resolution prompt template (must contain ``{entity_list}``).
    num_threads : int
        Concurrency limit for LLM calls (reserved for future use).

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        Updated ``(entities, relationships)`` with unified titles and an
        ``alternative_names`` column on entities.
    """
    if "title" not in entities.columns:
        return entities, relationships

    titles = entities["title"].dropna().unique().tolist()
    if len(titles) < 2:
        return entities, relationships

    logger.info(
        "Running LLM entity resolution on %d unique entity names...", len(titles)
    )

    # Build numbered entity list for the prompt
    entity_list = "\n".join(f"{i+1}. {name}" for i, name in enumerate(titles))
    formatted_prompt = prompt.format(entity_list=entity_list)

    try:
        response = await model.completion_async(messages=formatted_prompt)
        raw = (response.content or "").strip()
    except Exception as e:
        logger.warning("Entity resolution LLM call failed, skipping resolution: %s", e, exc_info=True)
        return entities, relationships

    if "NO_DUPLICATES" in raw:
        logger.info("Entity resolution: no duplicates found")
        return entities, relationships

    # Parse response and build rename mapping
    rename_map: dict[str, str] = {}  # alias → canonical
    alternatives: dict[str, set[str]] = {}  # canonical → {aliases}

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
                if 0 <= idx < len(titles):
                    indices.append(idx)
        if len(indices) >= 2:
            canonical = titles[indices[0]]
            if canonical not in alternatives:
                alternatives[canonical] = set()
            for alias_idx in indices[1:]:
                alias = titles[alias_idx]
                rename_map[alias] = canonical
                alternatives[canonical].add(alias)
                logger.info("  Entity resolution: '%s' → '%s'", alias, canonical)

    if not rename_map:
        logger.info("Entity resolution complete: no duplicates found")
        return entities, relationships

    logger.info("Entity resolution: merging %d duplicate names", len(rename_map))

    # Apply renames to entity titles
    entities = entities.copy()
    entities["title"] = entities["title"].map(lambda t: rename_map.get(t, t))

    # Add alternative_names column
    entities["alternative_names"] = entities["title"].map(
        lambda t: sorted(alternatives.get(t, set()))
    )

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
