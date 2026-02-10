# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import pandas as pd
from graphrag.index.run.utils import create_run_context
from graphrag.index.typing.context import PipelineRunContext
from pandas.testing import assert_series_equal

pd.set_option("display.max_columns", None)


async def create_test_context(storage: list[str] | None = None) -> PipelineRunContext:
    """Create a test context with tables loaded into storage storage."""
    context = create_run_context()

    # always set the input docs, but since our stored table is final, drop what wouldn't be in the original source input
    input = load_test_table("documents")
    input.drop(columns=["text_unit_ids"], inplace=True)
    await context.output_table_provider.write_dataframe("documents", input)

    if storage:
        for name in storage:
            table = load_test_table(name)
            await context.output_table_provider.write_dataframe(name, table)

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
        try:
            assert column in actual.columns
        except AssertionError:
            print(f"Column '{column}' not found in actual output.")
        try:
            # dtypes can differ since the test data is read from parquet and our workflow runs in memory
            if column != "id":  # don't check uuids
                assert_series_equal(
                    actual[column],
                    expected[column],
                    check_dtype=False,
                    check_index=False,
                )
        except AssertionError:
            print(f"Column '{column}' does not match.")
            print("Expected:")
            print(expected[column])
            print("Actual:")
            print(actual[column])
            raise
