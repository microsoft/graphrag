# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Shared helpers for temporal evidence fields."""

from typing import Any


def fill_temporal_evidence_defaults(row: dict[str, Any]) -> None:
    """Fill missing temporal evidence defaults from text_unit_ids."""
    text_unit_ids = row.get("text_unit_ids") or []
    if not row.get("evidence_count"):
        row["evidence_count"] = len(text_unit_ids)
    if text_unit_ids and not row.get("first_seen_text_unit_id"):
        row["first_seen_text_unit_id"] = text_unit_ids[0]
    if text_unit_ids and not row.get("last_seen_text_unit_id"):
        row["last_seen_text_unit_id"] = text_unit_ids[-1]
