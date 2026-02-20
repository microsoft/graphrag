# Copyright (C) 2026 Microsoft

"""Tests for CSVTable temp-file write strategy and streaming behavior.

When truncate=True, CSVTable writes to a temporary file and moves it
over the original on close(). This allows safe concurrent reads from
the original while writes are in progress — the pattern used by
create_final_text_units where the same file is read and written.
"""

import csv
from pathlib import Path
from typing import Any

import pytest
from graphrag_storage.file_storage import FileStorage
from graphrag_storage.tables.csv_table import CSVTable


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    """Read all rows from a CSV file as dicts."""
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_seed_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write seed rows to a CSV file for test setup."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


class TestCSVTableTruncateWrite:
    """Verify the temp-file write strategy when truncate=True."""

    @pytest.fixture
    def storage(self, tmp_path: Path) -> FileStorage:
        """Create a FileStorage rooted at a temp directory."""
        return FileStorage(base_dir=str(tmp_path))

    @pytest.fixture
    def seed_file(
        self,
        storage: FileStorage,
        tmp_path: Path,
    ) -> Path:
        """Seed a text_units.csv file with original data."""
        rows = [
            {"id": "tu1", "text": "original1"},
            {"id": "tu2", "text": "original2"},
        ]
        file_path = tmp_path / "text_units.csv"
        _write_seed_csv(file_path, rows)
        return file_path

    async def test_original_readable_during_writes(
        self,
        storage: FileStorage,
        seed_file: Path,
    ):
        """The original file remains intact while writes go to a temp file."""
        table = CSVTable(storage, "text_units", truncate=True)
        await table.write({"id": "tu_new", "text": "replaced"})

        original_rows = _read_csv_rows(seed_file)
        assert len(original_rows) == 2
        assert original_rows[0]["id"] == "tu1"
        assert original_rows[1]["id"] == "tu2"

        await table.close()

    async def test_temp_file_replaces_original_on_close(
        self,
        storage: FileStorage,
        seed_file: Path,
    ):
        """After close(), the original file contains only the new data."""
        table = CSVTable(storage, "text_units", truncate=True)
        await table.write({"id": "tu_new", "text": "replaced"})
        await table.close()

        rows = _read_csv_rows(seed_file)
        assert len(rows) == 1
        assert rows[0]["id"] == "tu_new"
        assert rows[0]["text"] == "replaced"

    async def test_no_temp_file_left_after_close(
        self,
        storage: FileStorage,
        seed_file: Path,
    ):
        """No leftover temp files in the directory after close()."""
        table = CSVTable(storage, "text_units", truncate=True)
        await table.write({"id": "tu1", "text": "new"})
        await table.close()

        csv_files = list(seed_file.parent.glob("*.csv"))
        assert len(csv_files) == 1
        assert csv_files[0].name == "text_units.csv"

    async def test_multiple_writes_accumulate_in_temp(
        self,
        storage: FileStorage,
        seed_file: Path,
    ):
        """Multiple rows written before close() all appear in final file."""
        table = CSVTable(storage, "text_units", truncate=True)
        for i in range(5):
            await table.write({"id": f"tu{i}", "text": f"row{i}"})
        await table.close()

        rows = _read_csv_rows(seed_file)
        assert len(rows) == 5
        assert [r["id"] for r in rows] == [
            "tu0",
            "tu1",
            "tu2",
            "tu3",
            "tu4",
        ]

    async def test_concurrent_read_and_write_same_file(
        self,
        storage: FileStorage,
        seed_file: Path,
    ):
        """Simulates the create_final_text_units pattern: read from
        original while writing new rows, then close replaces the file."""
        reader = CSVTable(storage, "text_units", truncate=False)
        writer = CSVTable(storage, "text_units", truncate=True)

        original_rows: list[dict[str, Any]] = []
        async for row in reader:
            original_rows.append(row)
            await writer.write({
                "id": row["id"],
                "text": row["text"].upper(),
            })

        assert len(original_rows) == 2

        file_during_write = _read_csv_rows(seed_file)
        assert len(file_during_write) == 2
        assert file_during_write[0]["text"] == "original1"

        await writer.close()
        await reader.close()

        final_rows = _read_csv_rows(seed_file)
        assert len(final_rows) == 2
        assert final_rows[0]["text"] == "ORIGINAL1"
        assert final_rows[1]["text"] == "ORIGINAL2"


class TestCSVTableAppendWrite:
    """Verify append behavior when truncate=False."""

    @pytest.fixture
    def storage(self, tmp_path: Path) -> FileStorage:
        """Create a FileStorage rooted at a temp directory."""
        return FileStorage(base_dir=str(tmp_path))

    async def test_append_to_existing_file(
        self,
        storage: FileStorage,
        tmp_path: Path,
    ):
        """Appending to an existing file adds rows without header."""
        file_path = tmp_path / "data.csv"
        _write_seed_csv(file_path, [{"id": "r1", "val": "a"}])

        table = CSVTable(storage, "data", truncate=False)
        await table.write({"id": "r2", "val": "b"})
        await table.close()

        rows = _read_csv_rows(file_path)
        assert len(rows) == 2
        assert rows[0]["id"] == "r1"
        assert rows[1]["id"] == "r2"

    async def test_append_creates_file_with_header(
        self,
        storage: FileStorage,
        tmp_path: Path,
    ):
        """Appending to a non-existent file creates it with header."""
        table = CSVTable(storage, "new_table", truncate=False)
        await table.write({"id": "r1", "val": "x"})
        await table.close()

        file_path = tmp_path / "new_table.csv"
        rows = _read_csv_rows(file_path)
        assert len(rows) == 1
        assert rows[0]["id"] == "r1"

    async def test_no_temp_file_used_for_append(
        self,
        storage: FileStorage,
        tmp_path: Path,
    ):
        """Append mode writes directly, no temp file involved."""
        table = CSVTable(storage, "direct", truncate=False)
        await table.write({"id": "r1"})

        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1
        assert csv_files[0].name == "direct.csv"
        await table.close()


class TestCSVTableCloseIdempotent:
    """Verify close() can be called multiple times safely."""

    @pytest.fixture
    def storage(self, tmp_path: Path) -> FileStorage:
        """Create a FileStorage rooted at a temp directory."""
        return FileStorage(base_dir=str(tmp_path))

    async def test_double_close_is_safe(
        self,
        storage: FileStorage,
        tmp_path: Path,
    ):
        """Calling close() twice does not raise."""
        table = CSVTable(storage, "test", truncate=True)
        await table.write({"id": "r1"})
        await table.close()
        await table.close()

    async def test_close_without_writes_is_safe(
        self,
        storage: FileStorage,
    ):
        """Closing a table that was never written to is a no-op."""
        table = CSVTable(storage, "empty", truncate=True)
        await table.close()
