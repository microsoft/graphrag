# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import cast

import pandas as pd
from datashaper import Workflow
from pandas.testing import assert_series_equal

from graphrag.config import create_graphrag_config
from graphrag.index import (
    PipelineWorkflowConfig,
    create_pipeline_config,
)
from graphrag.index.run.utils import _create_run_context
from graphrag.index.storage.pipeline_storage import PipelineStorage

pd.set_option("display.max_columns", None)


def load_input_tables(inputs: list[str]) -> dict[str, pd.DataFrame]:
    """Harvest all the referenced input IDs from the workflow being tested and pass them here."""
    # stick all the inputs in a map - Workflow looks them up by name
    input_tables: dict[str, pd.DataFrame] = {}

    # all workflows implicitly receive the `input` source, which is formatted as a dataframe after loading from storage
    # we'll simulate that by just loading one of our output parquets and converting back to equivalent dataframe
    # so we aren't dealing with storage vagaries (which would become an integration test)
    source = pd.read_parquet("tests/verbs/data/create_final_documents.parquet")
    source.rename(columns={"raw_content": "text"}, inplace=True)
    input_tables["source"] = cast(pd.DataFrame, source[["id", "text", "title"]])

    for input in inputs:
        # remove the workflow: prefix if it exists, because that is not part of the actual table filename
        name = input.replace("workflow:", "")
        input_tables[input] = pd.read_parquet(f"tests/verbs/data/{name}.parquet")

    return input_tables


def load_expected(output: str) -> pd.DataFrame:
    """Pass in the workflow output (generally the workflow name)"""
    return pd.read_parquet(f"tests/verbs/data/{output}.parquet")


def get_config_for_workflow(name: str) -> PipelineWorkflowConfig:
    """Instantiates the bare minimum config to get a default workflow config for testing."""
    config = create_graphrag_config()

    # this flag needs to be set before creating the pipeline config, or the entire covariate workflow will be excluded
    config.claim_extraction.enabled = True

    pipeline_config = create_pipeline_config(config)

    result = next(conf for conf in pipeline_config.workflows if conf.name == name)

    return cast(PipelineWorkflowConfig, result.config)


async def get_workflow_output(
    input_tables: dict[str, pd.DataFrame],
    schema: dict,
    storage: PipelineStorage | None = None,
) -> pd.DataFrame:
    """Pass in the input tables, the schema, and the output name"""

    # the bare minimum workflow is the pipeline schema and table context
    workflow = Workflow(
        schema=schema,
        input_tables=input_tables,
    )

    context = _create_run_context(storage, None, None)

    await workflow.run(context=context)

    # if there's only one output, it is the default here, no name required
    return cast(pd.DataFrame, workflow.output())


def compare_outputs(
    actual: pd.DataFrame, expected: pd.DataFrame, columns: list[str] | None = None
) -> None:
    """Compare the actual and expected dataframes, optionally specifying columns to compare.
    This uses assert_series_equal since we are sometimes intentionally omitting columns from the actual output."""
    cols = expected.columns if columns is None else columns

    assert len(actual) == len(
        expected
    ), f"Expected: {len(expected)} rows, Actual: {len(actual)} rows"

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
