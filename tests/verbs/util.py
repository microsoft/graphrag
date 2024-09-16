# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import cast

import pandas as pd
from datashaper import Workflow


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


def compare_outputs(actual: pd.DataFrame, expected: pd.DataFrame) -> None:
    try:
        assert actual.shape == expected.shape
    except AssertionError:
        print("Expected:")
        print(expected.head())
        print("Actual:")
        print(actual.head())
        raise AssertionError from None
