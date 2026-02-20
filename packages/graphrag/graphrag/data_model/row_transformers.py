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
    nullable columns), keeping behaviour consistent with the
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
    return row


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
    ``rank`` -> float, ``findings`` -> list, ``size`` -> int.
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
    return row
