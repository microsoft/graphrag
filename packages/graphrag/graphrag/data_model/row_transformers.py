# Copyright (C) 2026 Microsoft

"""Row-level type coercion for streaming Table reads.

Each transformer converts a raw ``dict[str, Any]`` row (as produced by
``csv.DictReader``, where every value is a string) into a dict with
properly typed fields.  They serve the same purpose as the DataFrame-
based ``*_typed`` helpers in ``dfs.py``, but operate on single rows so
they can be passed as the *transformer* argument to
``TableProvider.open()``.
"""

from typing import Any

from graphrag.data_model.dfs import split_list_column


def _safe_int(value: Any, fill: int = -1) -> int:
    """Coerce a value to int, returning *fill* when missing or empty.

    Handles NaN from Parquet float-promoted nullable int columns
    (``row.to_dict()`` yields ``numpy.float64(nan)``) and any other
    non-convertible type.
    """
    if value is None or value == "":
        return fill
    try:
        return int(value)
    except (ValueError, TypeError):
        return fill


def _safe_float(value: Any, fill: float = 0.0) -> float:
    """Coerce a value to float, returning *fill* when missing or empty.

    Also applies *fill* when the value is NaN (e.g. from Parquet
    nullable columns), keeping behavior consistent with the
    DataFrame-level ``fillna(fill).astype(float)`` pattern.
    """
    if value is None or value == "":
        return fill
    try:
        result = float(value)
    except (ValueError, TypeError):
        return fill
    # math.isnan without importing math
    if result != result:
        return fill
    return result


def _coerce_list(value: Any) -> list[Any]:
    """Parse a value into a list, handling CSV string and array types.

    Handles three cases:
    - str: CSV-encoded list (e.g. from CSVTable rows)
    - list: already a Python list (pass-through)
    - array-like with ``tolist`` (e.g. numpy.ndarray from ParquetTable
      ``row.to_dict()``)
    """
    if isinstance(value, str):
        return split_list_column(value)
    if isinstance(value, list):
        return value
    if hasattr(value, "tolist"):
        return value.tolist()
    return []


def _coerce_temporal_evidence_row(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce shared temporal evidence columns on a single row."""
    if "first_seen_turn_index" in row:
        row["first_seen_turn_index"] = _safe_int(row["first_seen_turn_index"], 0)
    if "last_seen_turn_index" in row:
        row["last_seen_turn_index"] = _safe_int(row["last_seen_turn_index"], 0)
    if "evidence_count" in row:
        row["evidence_count"] = _safe_int(row["evidence_count"], 0)
    if "first_seen_timestamp" in row and row["first_seen_timestamp"] is not None:
        row["first_seen_timestamp"] = str(row["first_seen_timestamp"])
    if "last_seen_timestamp" in row and row["last_seen_timestamp"] is not None:
        row["last_seen_timestamp"] = str(row["last_seen_timestamp"])
    if "first_seen_text_unit_id" in row and row["first_seen_text_unit_id"] is not None:
        row["first_seen_text_unit_id"] = str(row["first_seen_text_unit_id"])
    if "last_seen_text_unit_id" in row and row["last_seen_text_unit_id"] is not None:
        row["last_seen_text_unit_id"] = str(row["last_seen_text_unit_id"])
    return row


# -- entities (mirrors entities_typed) ------------------------------------


def transform_entity_row(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce types for an entity row.

    Mirrors ``entities_typed``: ``human_readable_id`` -> int,
    ``text_unit_ids`` -> list, ``frequency`` -> int, ``degree`` -> int.
    """
    if "human_readable_id" in row:
        row["human_readable_id"] = _safe_int(
            row["human_readable_id"],
        )
    if "text_unit_ids" in row:
        row["text_unit_ids"] = _coerce_list(row["text_unit_ids"])
    if "frequency" in row:
        row["frequency"] = _safe_int(row["frequency"], 0)
    if "degree" in row:
        row["degree"] = _safe_int(row["degree"], 0)
    return _coerce_temporal_evidence_row(row)


def transform_entity_row_for_embedding(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Add a title_description column for embedding generation."""
    title = row.get("title") or ""
    description = row.get("description") or ""
    row["title_description"] = f"{title}:{description}"
    return row


# -- relationships (mirrors relationships_typed) --------------------------


def transform_relationship_row(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Coerce types for a relationship row.

    Mirrors ``relationships_typed``: ``human_readable_id`` -> int,
    ``weight`` -> float, ``combined_degree`` -> int,
    ``text_unit_ids`` -> list.
    """
    if "human_readable_id" in row:
        row["human_readable_id"] = _safe_int(
            row["human_readable_id"],
        )
    if "weight" in row:
        row["weight"] = _safe_float(row["weight"])
    if "combined_degree" in row:
        row["combined_degree"] = _safe_int(
            row["combined_degree"],
            0,
        )
    if "text_unit_ids" in row:
        row["text_unit_ids"] = _coerce_list(row["text_unit_ids"])
    return _coerce_temporal_evidence_row(row)


# -- communities (mirrors communities_typed) ------------------------------


def transform_community_row(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Coerce types for a community row.

    Mirrors ``communities_typed``: ``human_readable_id`` -> int,
    ``community`` -> int, ``level`` -> int, ``children`` -> list,
    ``entity_ids`` -> list, ``relationship_ids`` -> list,
    ``text_unit_ids`` -> list, ``period`` -> str, ``size`` -> int.
    """
    if "human_readable_id" in row:
        row["human_readable_id"] = _safe_int(
            row["human_readable_id"],
        )
    row["community"] = _safe_int(row.get("community"))
    row["level"] = _safe_int(row.get("level"))
    row["children"] = _coerce_list(row.get("children"))
    if "entity_ids" in row:
        row["entity_ids"] = _coerce_list(row["entity_ids"])
    if "relationship_ids" in row:
        row["relationship_ids"] = _coerce_list(
            row["relationship_ids"],
        )
    if "text_unit_ids" in row:
        row["text_unit_ids"] = _coerce_list(row["text_unit_ids"])
    row["period"] = str(row.get("period", ""))
    row["size"] = _safe_int(row.get("size"), 0)
    return row


# -- community reports (mirrors community_reports_typed) ------------------


def transform_community_report_row(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Coerce types for a community report row.

    Mirrors ``community_reports_typed``: ``human_readable_id`` -> int,
    ``community`` -> int, ``level`` -> int, ``children`` -> list,
    ``rank`` -> float, ``findings`` -> list, ``timeline_events`` -> list,
    ``superseded_facts`` -> list, ``date_range`` -> list, ``size`` -> int.
    """
    if "human_readable_id" in row:
        row["human_readable_id"] = _safe_int(
            row["human_readable_id"],
        )
    row["community"] = _safe_int(row.get("community"))
    row["level"] = _safe_int(row.get("level"))
    row["children"] = _coerce_list(row.get("children"))
    row["rank"] = _safe_float(row.get("rank"))
    row["findings"] = _coerce_list(row.get("findings"))
    if "timeline_events" in row:
        row["timeline_events"] = _coerce_list(row.get("timeline_events"))
    if "superseded_facts" in row:
        row["superseded_facts"] = _coerce_list(row.get("superseded_facts"))
    if "date_range" in row:
        row["date_range"] = _coerce_list(row.get("date_range"))
    if "current_state" in row and row["current_state"] is not None:
        row["current_state"] = str(row["current_state"])
    row["size"] = _safe_int(row.get("size"), 0)
    return row


# -- covariates (mirrors covariates_typed) --------------------------------


def transform_covariate_row(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Coerce types for a covariate row.

    Mirrors ``covariates_typed``: ``human_readable_id`` -> int.
    """
    if "human_readable_id" in row:
        row["human_readable_id"] = _safe_int(
            row["human_readable_id"],
        )
    return row


# -- text units (mirrors text_units_typed) --------------------------------


def transform_text_unit_row(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Coerce types for a text-unit row.

    Mirrors ``text_units_typed``: ``human_readable_id`` -> int,
    ``n_tokens`` -> int, ``entity_ids`` -> list,
    ``relationship_ids`` -> list, ``covariate_ids`` -> list.
    """
    if "human_readable_id" in row:
        row["human_readable_id"] = _safe_int(
            row["human_readable_id"],
        )
    row["n_tokens"] = _safe_int(row.get("n_tokens"), 0)
    if "entity_ids" in row:
        row["entity_ids"] = _coerce_list(row["entity_ids"])
    if "relationship_ids" in row:
        row["relationship_ids"] = _coerce_list(
            row["relationship_ids"],
        )
    if "covariate_ids" in row:
        row["covariate_ids"] = _coerce_list(
            row["covariate_ids"],
        )
    if "turn_index" in row:
        row["turn_index"] = _safe_int(row.get("turn_index"), 0)
    if "start_turn_index" in row:
        row["start_turn_index"] = _safe_int(row.get("start_turn_index"), 0)
    if "end_turn_index" in row:
        row["end_turn_index"] = _safe_int(row.get("end_turn_index"), 0)
    if "turn_timestamp" in row and row["turn_timestamp"] is not None:
        row["turn_timestamp"] = str(row["turn_timestamp"])
    if "turn_timestamp_start" in row and row["turn_timestamp_start"] is not None:
        row["turn_timestamp_start"] = str(row["turn_timestamp_start"])
    if "turn_timestamp_end" in row and row["turn_timestamp_end"] is not None:
        row["turn_timestamp_end"] = str(row["turn_timestamp_end"])
    if "turn_role" in row and row["turn_role"] is not None:
        row["turn_role"] = str(row["turn_role"])
    if "included_roles" in row:
        row["included_roles"] = _coerce_list(row["included_roles"])
    if "chunk_index_in_document" in row:
        row["chunk_index_in_document"] = _safe_int(row.get("chunk_index_in_document"), 0)
    if "chunk_index_in_conversation" in row:
        row["chunk_index_in_conversation"] = _safe_int(
            row.get("chunk_index_in_conversation"),
            0,
        )
    if "conversation_id" in row and row["conversation_id"] is not None:
        row["conversation_id"] = str(row["conversation_id"])
    return row


# -- documents (mirrors documents_typed) ----------------------------------


def transform_document_row(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Coerce types for a document row.

    Mirrors ``documents_typed``: ``human_readable_id`` -> int,
    ``text_unit_ids`` -> list.
    """
    if "human_readable_id" in row:
        row["human_readable_id"] = _safe_int(
            row["human_readable_id"],
        )
    if "text_unit_ids" in row:
        row["text_unit_ids"] = _coerce_list(row["text_unit_ids"])
    if "turn_index" in row:
        row["turn_index"] = _safe_int(row.get("turn_index"), 0)
    if "turn_timestamp" in row and row["turn_timestamp"] is not None:
        row["turn_timestamp"] = str(row["turn_timestamp"])
    if "turn_role" in row and row["turn_role"] is not None:
        row["turn_role"] = str(row["turn_role"])
    if "conversation_id" in row and row["conversation_id"] is not None:
        row["conversation_id"] = str(row["conversation_id"])
    return row
