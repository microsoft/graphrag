# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import Any

import pandas as pd
from graphrag.data_model.row_transformers import (
    transform_entity_row,
    transform_relationship_row,
    transform_text_unit_row,
)
from graphrag.data_model.schemas import TEXT_UNITS_FINAL_COLUMNS
from graphrag.index.workflows.create_final_text_units import (
    create_final_text_units,
    run_workflow,
)
from graphrag_storage.file_storage import FileStorage
from graphrag_storage.tables.csv_table import CSVTable
from graphrag_storage.tables.table import Table

from tests.unit.config.utils import get_default_graphrag_config

from .util import (
    compare_outputs,
    create_test_context,
    load_test_table,
)

# ---------------------------------------------------------------------------
# Minimal in-memory write table (shared by both test paths)
# ---------------------------------------------------------------------------


class _FakeWriteTable(Table):
    """In-memory write-only table that collects rows."""

    def __init__(self) -> None:
        """Initialise with an empty row store."""
        self.rows: list[dict[str, Any]] = []

    async def write(self, row: dict[str, Any]) -> None:
        """Append a row."""
        self.rows.append(row)

    def __aiter__(self):
        """Not supported."""
        raise NotImplementedError

    async def length(self) -> int:
        """Return the number of written rows."""
        return len(self.rows)

    async def has(self, row_id: str) -> bool:
        """Check written rows for a matching id."""
        return any(r.get("id") == row_id for r in self.rows)

    async def close(self) -> None:
        """No-op."""


# ---------------------------------------------------------------------------
# Parquet-based integration test (exercises run_workflow)
# ---------------------------------------------------------------------------


async def test_create_final_text_units():
    """End-to-end test using ParquetTableProvider via run_workflow."""
    expected = load_test_table("text_units")

    context = await create_test_context(
        storage=[
            "text_units",
            "entities",
            "relationships",
            "covariates",
        ],
    )

    config = get_default_graphrag_config()
    config.extract_claims.enabled = True

    await run_workflow(config, context)

    actual = await context.output_table_provider.read_dataframe("text_units")

    for column in TEXT_UNITS_FINAL_COLUMNS:
        assert column in actual.columns

    compare_outputs(actual, expected)


# ---------------------------------------------------------------------------
# CSV-path test (real CSVTable + FileStorage + row transformers)
# ---------------------------------------------------------------------------


async def test_create_final_text_units_csv_path():
    """Exercise create_final_text_units through real CSVTable reads.

    Reads the CSV fixture files in tests/verbs/data/ (which use the
    pandas/numpy newline-separated list format) via CSVTable with the
    same row transformers used by run_workflow. This exercises the full
    CSV round-trip including backwards-compatible list parsing.
    """
    expected_df = load_test_table("text_units")

    storage = FileStorage("tests/verbs/data")

    text_units_table = CSVTable(
        storage,
        "text_units",
        transformer=transform_text_unit_row,
    )
    entities_table = CSVTable(
        storage,
        "entities",
        transformer=transform_entity_row,
    )
    relationships_table = CSVTable(
        storage,
        "relationships",
        transformer=transform_relationship_row,
    )
    covariates_table = CSVTable(storage, "covariates")
    output = _FakeWriteTable()

    await create_final_text_units(
        text_units_table,
        entities_table,
        relationships_table,
        output,
        covariates_table,
    )

    assert len(output.rows) == len(expected_df)

    actual_df = pd.DataFrame(output.rows)
    for column in TEXT_UNITS_FINAL_COLUMNS:
        assert column in actual_df.columns

    compare_outputs(actual_df, expected_df)
