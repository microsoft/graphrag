# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for the timestamp module (no backend required)."""

import pytest
from graphrag_vectors.timestamp import (
    TIMESTAMP_FIELDS,
    _timestamp_fields_for,
    explode_timestamp,
)


class TestExplodeTimestamp:
    """Tests for explode_timestamp()."""

    def test_basic_explosion(self):
        result = explode_timestamp("2024-03-15T14:30:00", "created")
        assert result["created_year"] == 2024
        assert result["created_month"] == 3
        assert result["created_month_name"] == "March"
        assert result["created_day"] == 15
        assert result["created_day_of_week"] == "Friday"
        assert result["created_hour"] == 14
        assert result["created_quarter"] == 1

    def test_all_keys_present(self):
        result = explode_timestamp("2024-01-01T00:00:00", "ts")
        expected_keys = {
            "ts_year",
            "ts_month",
            "ts_month_name",
            "ts_day",
            "ts_day_of_week",
            "ts_hour",
            "ts_quarter",
        }
        assert set(result.keys()) == expected_keys

    def test_empty_string_returns_empty(self):
        result = explode_timestamp("", "ts")
        assert result == {}

    def test_none_returns_empty(self):
        result = explode_timestamp(None, "ts")
        assert result == {}


class TestExplodeTimestampQuarterBoundaries:
    """Tests for correct quarter assignment across all months."""

    @pytest.mark.parametrize(
        ("month", "expected_quarter"),
        [
            ("01", 1),
            ("02", 1),
            ("03", 1),
            ("04", 2),
            ("05", 2),
            ("06", 2),
            ("07", 3),
            ("08", 3),
            ("09", 3),
            ("10", 4),
            ("11", 4),
            ("12", 4),
        ],
    )
    def test_quarter(self, month, expected_quarter):
        result = explode_timestamp(f"2024-{month}-15T12:00:00", "d")
        assert result["d_quarter"] == expected_quarter


class TestTimestampFieldsForPrefix:
    """Tests for _timestamp_fields_for() helper."""

    def test_produces_correct_keys(self):
        fields = _timestamp_fields_for("mydate")
        expected_keys = {
            "mydate_year",
            "mydate_month",
            "mydate_month_name",
            "mydate_day",
            "mydate_day_of_week",
            "mydate_hour",
            "mydate_quarter",
        }
        assert set(fields.keys()) == expected_keys

    def test_types(self):
        fields = _timestamp_fields_for("ts")
        assert fields["ts_year"] == "int"
        assert fields["ts_month"] == "int"
        assert fields["ts_month_name"] == "str"
        assert fields["ts_day"] == "int"
        assert fields["ts_day_of_week"] == "str"
        assert fields["ts_hour"] == "int"
        assert fields["ts_quarter"] == "int"


class TestTimestampFieldsConstant:
    """Tests for the TIMESTAMP_FIELDS combined constant."""

    def test_contains_create_and_update_fields(self):
        assert "create_date_year" in TIMESTAMP_FIELDS
        assert "update_date_year" in TIMESTAMP_FIELDS
        assert "create_date_month_name" in TIMESTAMP_FIELDS
        assert "update_date_month_name" in TIMESTAMP_FIELDS

    def test_total_count(self):
        # 7 fields * 2 prefixes = 14
        assert len(TIMESTAMP_FIELDS) == 14
