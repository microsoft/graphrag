# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import pandas as pd
from pandas.testing import assert_series_equal

import graphrag.config.defaults as defs
from graphrag.index.run.utils import create_run_context
from graphrag.index.typing.context import PipelineRunContext
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

pd.set_option("display.max_columns", None)

FAKE_API_KEY = "NOT_AN_API_KEY"

DEFAULT_CHAT_MODEL_CONFIG = {
    "api_key": FAKE_API_KEY,
    "type": defs.DEFAULT_CHAT_MODEL_TYPE.value,
    "model": defs.DEFAULT_CHAT_MODEL,
}

DEFAULT_EMBEDDING_MODEL_CONFIG = {
    "api_key": FAKE_API_KEY,
    "type": defs.DEFAULT_EMBEDDING_MODEL_TYPE.value,
    "model": defs.DEFAULT_EMBEDDING_MODEL,
}

DEFAULT_MODEL_CONFIG = {
    defs.DEFAULT_CHAT_MODEL_ID: DEFAULT_CHAT_MODEL_CONFIG,
    defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
}


async def create_test_context(storage: list[str] | None = None) -> PipelineRunContext:
    """Create a test context with tables loaded into storage storage."""
    context = create_run_context()

    # always set the input docs, but since our stored table is final, drop what wouldn't be in the original source input
    input = load_test_table("documents")
    input.drop(columns=["text_unit_ids"], inplace=True)
    await write_table_to_storage(input, "documents", context.storage)

    if storage:
        for name in storage:
            table = load_test_table(name)
            await write_table_to_storage(table, name, context.storage)

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
            if column != "id":  # don't check uuids
                assert_series_equal(
                    actual[column],
                    expected[column],
                    check_dtype=False,
                    check_index=False,
                )
        except AssertionError:
            print("Expected:")
            print(expected[column])
            print("Actual:")
            print(actual[column])
            raise


async def update_document_metadata(metadata: list[str], context: PipelineRunContext):
    """Takes the default documents and adds the configured metadata columns for later parsing by the text units and final documents workflows."""
    documents = await load_table_from_storage("documents", context.storage)
    documents["metadata"] = documents[metadata].apply(lambda row: row.to_dict(), axis=1)
    await write_table_to_storage(
        documents, "documents", context.storage
    )  # write to the runtime context storage only
