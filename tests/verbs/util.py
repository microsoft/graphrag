# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import pandas as pd
from pandas.testing import assert_series_equal

from graphrag.index.context import PipelineRunContext
from graphrag.index.run.utils import create_run_context

pd.set_option("display.max_columns", None)


async def create_test_context(
    storage: list[str] | None = None,
    runtime_storage: list[str] | None = None,
) -> PipelineRunContext:
    """Create a test context with tables loaded into storage and runtime storage."""
    context = create_run_context(None, None, None)

    # always set the input docs
    input = pd.read_parquet("tests/verbs/data/source_documents.parquet")
    await context.runtime_storage.set("input", input)

    if storage:
        for name in storage:
            table = load_test_table(name)
            # normal storage interface insists on bytes
            await context.storage.set(f"{name}.parquet", table.to_parquet())

    if runtime_storage:
        for name in runtime_storage:
            table = load_test_table(name)
            # runtime storage doesn't care what is in there
            await context.runtime_storage.set(name, table)

    return context


def load_test_table(output: str) -> pd.DataFrame:
    """Pass in the workflow output (generally the workflow name)"""
    return pd.read_parquet(f"tests/verbs/data/{output}.parquet")


def compare_outputs(
    actual: pd.DataFrame, expected: pd.DataFrame, columns: list[str] | None = None
) -> None:
    """Compare the actual and expected dataframes, optionally specifying columns to compare.
    This uses assert_series_equal since we are sometimes intentionally omitting columns from the actual output.
    """
    cols = expected.columns if columns is None else columns

    assert len(actual) == len(expected), (
        f"Expected: {len(expected)} rows, Actual: {len(actual)} rows"
    )

    for column in cols:
        assert column in actual.columns
        try:
            # dtypes can differ since the test data is read from parquet and our workflow runs in memory
            assert_series_equal(
                actual[column], expected[column], check_dtype=False, check_index=False
            )
        except AssertionError:
            print("Expected:")
            print(expected[column])
            print("Actual:")
            print(actual[column])
            raise
