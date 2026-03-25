# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing extract_graph method."""

import logging
from typing import TYPE_CHECKING

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.data_model.schemas import (
    CONVERSATION_ID,
    END_TURN_INDEX,
    FIRST_SEEN_TEXT_UNIT_ID,
    FIRST_SEEN_TIMESTAMP,
    FIRST_SEEN_TURN_INDEX,
    INCLUDED_ROLES,
    LAST_SEEN_TEXT_UNIT_ID,
    LAST_SEEN_TIMESTAMP,
    LAST_SEEN_TURN_INDEX,
    START_TURN_INDEX,
    TURN_TIMESTAMP_END,
    TURN_TIMESTAMP_START,
    EVIDENCE_COUNT,
    CHUNK_INDEX_IN_CONVERSATION,
    CHUNK_INDEX_IN_DOCUMENT,
)
from graphrag.index.operations.extract_graph.graph_extractor import GraphExtractor
from graphrag.index.operations.extract_graph.utils import filter_orphan_relationships
from graphrag.index.utils.derive_from_rows import derive_from_rows
from graphrag.index.utils.temporal_trace import trace_event

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion

logger = logging.getLogger(__name__)


async def extract_graph(
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    text_column: str,
    id_column: str,
    model: "LLMCompletion",
    prompt: str,
    entity_types: list[str],
    max_gleanings: int,
    num_threads: int,
    async_type: AsyncType,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract a graph from a piece of text using a language model."""
    num_started = 0
    trace_event(
        logger,
        stage="graph_extraction",
        event="extraction_start",
        text_unit_count=len(text_units),
    )

    async def run_strategy(row):
        nonlocal num_started
        text = row[text_column]
        text = _attach_temporal_header(text=text, row=row)
        id = row[id_column]
        trace_event(
            logger,
            stage="graph_extraction",
            event="text_unit_input",
            text_unit_id=id,
            conversation_id=_safe_str(row.get(CONVERSATION_ID)),
            start_turn_index=_safe_int(row.get(START_TURN_INDEX)),
            end_turn_index=_safe_int(row.get(END_TURN_INDEX)),
            turn_timestamp_start=_safe_str(row.get(TURN_TIMESTAMP_START)),
            turn_timestamp_end=_safe_str(row.get(TURN_TIMESTAMP_END)),
            preview_fields={"temporal_prompt_input": text},
        )
        result = await _run_extract_graph(
            text=text,
            source_id=id,
            entity_types=entity_types,
            model=model,
            prompt=prompt,
            max_gleanings=max_gleanings,
        )
        num_started += 1
        return result

    results = await derive_from_rows(
        text_units,
        run_strategy,
        callbacks,
        num_threads=num_threads,
        async_type=async_type,
        progress_msg="extract graph progress: ",
    )

    entity_dfs = []
    relationship_dfs = []
    for result in results:
        if result:
            entity_dfs.append(result[0])
            relationship_dfs.append(result[1])

    temporal_index = _build_temporal_index(text_units, id_column)
    trace_event(
        logger,
        stage="graph_extraction",
        event="temporal_index_built",
        extracted_rows=len(results),
        temporal_index_entries=len(temporal_index),
    )
    entities = _merge_entities(entity_dfs, temporal_index)
    relationships = _merge_relationships(relationship_dfs, temporal_index)
    relationships = filter_orphan_relationships(relationships, entities)
    trace_event(
        logger,
        stage="graph_extraction",
        event="merge_complete",
        merged_entities=len(entities),
        merged_relationships=len(relationships),
    )

    return (entities, relationships)


async def _run_extract_graph(
    text: str,
    source_id: str,
    entity_types: list[str],
    model: "LLMCompletion",
    prompt: str,
    max_gleanings: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the graph intelligence entity extraction strategy."""
    extractor = GraphExtractor(
        model=model,
        prompt=prompt,
        max_gleanings=max_gleanings,
        on_error=lambda e, s, d: logger.error(
            "Entity Extraction Error", exc_info=e, extra={"stack": s, "details": d}
        ),
    )
    text = text.strip()

    entities_df, relationships_df = await extractor(
        text,
        entity_types=entity_types,
        source_id=source_id,
    )

    return (entities_df, relationships_df)


def _merge_entities(
    entity_dfs,
    temporal_index: dict[str, dict[str, str | int | None]] | None = None,
) -> pd.DataFrame:
    all_entities = pd.concat(entity_dfs, ignore_index=True)
    merged = (
        all_entities
        .groupby(["title", "type"], sort=False)
        .agg(
            description=("description", list),
            text_unit_ids=("source_id", list),
            frequency=("source_id", "count"),
        )
        .reset_index()
    )
    return _apply_temporal_evidence(merged, temporal_index or {})


def _merge_relationships(
    relationship_dfs,
    temporal_index: dict[str, dict[str, str | int | None]] | None = None,
) -> pd.DataFrame:
    all_relationships = pd.concat(relationship_dfs, ignore_index=False)
    merged = (
        all_relationships
        .groupby(["source", "target"], sort=False)
        .agg(
            description=("description", list),
            text_unit_ids=("source_id", list),
            weight=("weight", "sum"),
        )
        .reset_index()
    )
    return _apply_temporal_evidence(merged, temporal_index or {})


def _attach_temporal_header(text: str, row: pd.Series) -> str:
    """Attach temporal metadata header for extraction prompt input."""
    header_lines: list[str] = []
    conversation_id = _safe_str(row.get(CONVERSATION_ID))
    if conversation_id:
        header_lines.append(f"conversation_id: {conversation_id}")

    start_turn = _safe_int(row.get(START_TURN_INDEX))
    end_turn = _safe_int(row.get(END_TURN_INDEX))
    if start_turn is not None and end_turn is not None:
        header_lines.append(f"turn_range: {start_turn}-{end_turn}")

    ts_start = _safe_str(row.get(TURN_TIMESTAMP_START))
    ts_end = _safe_str(row.get(TURN_TIMESTAMP_END))
    if ts_start and ts_end:
        header_lines.append(f"timestamp_range: {ts_start} -> {ts_end}")

    roles = _normalize_roles(row.get(INCLUDED_ROLES))
    if roles:
        header_lines.append(f"included_roles: {', '.join(roles)}")

    if not header_lines:
        return text
    return (
        "[TEMPORAL_CONTEXT]\n"
        + "\n".join(header_lines)
        + "\n[/TEMPORAL_CONTEXT]\n\n"
        + text
    )


def _build_temporal_index(
    text_units: pd.DataFrame,
    id_column: str,
) -> dict[str, dict[str, str | int | None]]:
    temporal_index: dict[str, dict[str, str | int | None]] = {}
    if id_column not in text_units.columns:
        return temporal_index
    for _, row in text_units.iterrows():
        row_id = _safe_str(row.get(id_column))
        if not row_id:
            continue
        temporal_index[row_id] = {
            CONVERSATION_ID: _safe_str(row.get(CONVERSATION_ID)),
            START_TURN_INDEX: _safe_int(row.get(START_TURN_INDEX)),
            END_TURN_INDEX: _safe_int(row.get(END_TURN_INDEX)),
            TURN_TIMESTAMP_START: _safe_str(row.get(TURN_TIMESTAMP_START)),
            TURN_TIMESTAMP_END: _safe_str(row.get(TURN_TIMESTAMP_END)),
            CHUNK_INDEX_IN_CONVERSATION: _safe_int(row.get(CHUNK_INDEX_IN_CONVERSATION)),
            CHUNK_INDEX_IN_DOCUMENT: _safe_int(row.get(CHUNK_INDEX_IN_DOCUMENT)),
        }
    return temporal_index


def _apply_temporal_evidence(
    merged: pd.DataFrame,
    temporal_index: dict[str, dict[str, str | int | None]],
) -> pd.DataFrame:
    if merged.empty:
        return merged

    merged["text_unit_ids"] = merged["text_unit_ids"].apply(
        lambda ids: _sorted_unique_ids(ids, temporal_index)
    )
    merged[EVIDENCE_COUNT] = merged["text_unit_ids"].apply(len)
    merged[FIRST_SEEN_TEXT_UNIT_ID] = merged["text_unit_ids"].apply(
        lambda ids: ids[0] if ids else None
    )
    merged[LAST_SEEN_TEXT_UNIT_ID] = merged["text_unit_ids"].apply(
        lambda ids: ids[-1] if ids else None
    )
    merged[FIRST_SEEN_TURN_INDEX] = merged[FIRST_SEEN_TEXT_UNIT_ID].apply(
        lambda tid: temporal_index.get(tid, {}).get(START_TURN_INDEX) if tid else None
    )
    merged[LAST_SEEN_TURN_INDEX] = merged[LAST_SEEN_TEXT_UNIT_ID].apply(
        lambda tid: temporal_index.get(tid, {}).get(END_TURN_INDEX) if tid else None
    )
    merged[FIRST_SEEN_TIMESTAMP] = merged[FIRST_SEEN_TEXT_UNIT_ID].apply(
        lambda tid: temporal_index.get(tid, {}).get(TURN_TIMESTAMP_START) if tid else None
    )
    merged[LAST_SEEN_TIMESTAMP] = merged[LAST_SEEN_TEXT_UNIT_ID].apply(
        lambda tid: temporal_index.get(tid, {}).get(TURN_TIMESTAMP_END) if tid else None
    )
    preview_columns = [
        "text_unit_ids",
        EVIDENCE_COUNT,
        FIRST_SEEN_TURN_INDEX,
        LAST_SEEN_TURN_INDEX,
        FIRST_SEEN_TIMESTAMP,
        LAST_SEEN_TIMESTAMP,
    ]
    preview = merged[preview_columns].head(5).to_dict("records")
    trace_event(
        logger,
        stage="graph_merge_finalize",
        event="temporal_evidence_assigned",
        record_count=len(merged),
        preview_records=preview,
    )
    return merged


def _sorted_unique_ids(
    ids: list[str] | None,
    temporal_index: dict[str, dict[str, str | int | None]],
) -> list[str]:
    if not ids:
        return []
    unique = list(dict.fromkeys(str(item) for item in ids))
    return sorted(unique, key=lambda tid: _temporal_sort_key(tid, temporal_index))


def _temporal_sort_key(
    text_unit_id: str,
    temporal_index: dict[str, dict[str, str | int | None]],
) -> tuple[str, int, str, int, int, str]:
    metadata = temporal_index.get(text_unit_id, {})
    return (
        str(metadata.get(CONVERSATION_ID) or "~"),
        int(metadata.get(START_TURN_INDEX) or 10**12),
        str(metadata.get(TURN_TIMESTAMP_START) or "~"),
        int(metadata.get(CHUNK_INDEX_IN_CONVERSATION) or 10**12),
        int(metadata.get(CHUNK_INDEX_IN_DOCUMENT) or 10**12),
        text_unit_id,
    )


def _safe_int(value: object) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_str(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _normalize_roles(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    text = text.strip("[]")
    return [item.strip().strip("'").strip('"') for item in text.split(",") if item.strip()]
