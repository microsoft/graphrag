# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.operations.temporal_evidence import fill_temporal_evidence_defaults


def test_fill_temporal_evidence_defaults_sets_values_from_text_units():
    row = {"text_unit_ids": ["tu1", "tu2", "tu3"]}

    fill_temporal_evidence_defaults(row)

    assert row["evidence_count"] == 3
    assert row["first_seen_text_unit_id"] == "tu1"
    assert row["last_seen_text_unit_id"] == "tu3"


def test_fill_temporal_evidence_defaults_keeps_existing_values():
    row = {
        "text_unit_ids": ["tu1", "tu2"],
        "evidence_count": 10,
        "first_seen_text_unit_id": "existing-first",
        "last_seen_text_unit_id": "existing-last",
    }

    fill_temporal_evidence_defaults(row)

    assert row["evidence_count"] == 10
    assert row["first_seen_text_unit_id"] == "existing-first"
    assert row["last_seen_text_unit_id"] == "existing-last"
