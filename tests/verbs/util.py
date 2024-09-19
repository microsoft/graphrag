# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import cast

import pandas as pd
from datashaper import Workflow
from pandas.testing import assert_series_equal

from graphrag.config import create_graphrag_config
from graphrag.index import (
    PipelineWorkflowConfig,
    PipelineWorkflowStep,
    create_pipeline_config,
)


def load_input_tables(inputs: list[str]) -> dict[str, pd.DataFrame]:
    """Harvest all the referenced input IDs from the workflow being tested and pass them here."""
    # stick all the inputs in a map - Workflow looks them up by name
    input_tables: dict[str, pd.DataFrame] = {}
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
    pipeline_config = create_pipeline_config(config)
    print(pipeline_config.workflows)
    result = next(conf for conf in pipeline_config.workflows if conf.name == name)
    return cast(PipelineWorkflowConfig, result.config)


async def get_workflow_output(
    input_tables: dict[str, pd.DataFrame], schema: dict
) -> pd.DataFrame:
    """Pass in the input tables, the schema, and the output name"""

    # the bare minimum workflow is the pipeline schema and table context
    workflow = Workflow(
        schema=schema,
        input_tables=input_tables,
    )

    await workflow.run()

    # if there's only one output, it is the default here, no name required
    return cast(pd.DataFrame, workflow.output())


def compare_outputs(
    actual: pd.DataFrame, expected: pd.DataFrame, columns: list[str] | None = None
) -> None:
    """Compare the actual and expected dataframes, optionally specifying columns to compare.
    This uses assert_series_equal since we are sometimes intentionally omitting columns from the actual output."""
    cols = expected.columns if columns is None else columns
    try:
        assert len(actual) == len(expected)
        assert len(actual.columns) == len(cols)
        for column in cols:
            # dtypes can differ since the test data is read from parquet and our workflow runs in memory
            assert_series_equal(actual[column], expected[column], check_dtype=False)
    except AssertionError:
        print("Expected:")
        print(expected.head())
        print("Actual:")
        print(actual.head())
        raise


def remove_disabled_steps(
    steps: list[PipelineWorkflowStep],
) -> list[PipelineWorkflowStep]:
    return [step for step in steps if step.get("enabled", True)]
