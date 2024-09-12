# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

import pandas as pd

from graphrag.index import run_pipeline, run_pipeline_with_config
from graphrag.index.config import PipelineWorkflowReference

# Our fake dataset
dataset = pd.DataFrame([
    {"type": "A", "col1": 2, "col2": 4},
    {"type": "A", "col1": 5, "col2": 10},
    {"type": "A", "col1": 15, "col2": 26},
    {"type": "B", "col1": 6, "col2": 15},
])


async def run_with_config():
    """Run a pipeline with a config file"""
    # load pipeline.yml in this directory
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "./pipeline.yml"
    )

    tables = []
    async for table in run_pipeline_with_config(
        config_or_path=config_path, dataset=dataset
    ):
        tables.append(table)
    pipeline_result = tables[-1]

    if pipeline_result.result is not None:
        # Should look something like this, which should be identical to the python example:
        #     type  aggregated_output
        # 0    A                448
        # 1    B                 90
        print(pipeline_result.result)
    else:
        print("No results!")


async def run_python():
    workflows: list[PipelineWorkflowReference] = [
        PipelineWorkflowReference(
            name="aggregate_workflow",
            steps=[
                {
                    "verb": "aggregate",  # https://github.com/microsoft/datashaper/blob/main/python/datashaper/datashaper/verbs/aggregate.py
                    "args": {
                        "groupby": "type",
                        "column": "col_multiplied",
                        "to": "aggregated_output",
                        "operation": "sum",
                    },
                    "input": {
                        "source": "workflow:derive_workflow",  # reference the derive_workflow, cause this one requires that one to run first
                        # Notice, these are out of order, the indexing engine will figure out the right order to run them in
                    },
                }
            ],
        ),
        PipelineWorkflowReference(
            name="derive_workflow",
            steps=[
                {
                    # built-in verb
                    "verb": "derive",  # https://github.com/microsoft/datashaper/blob/main/python/datashaper/datashaper/verbs/derive.py
                    "args": {
                        "column1": "col1",  # from above
                        "column2": "col2",  # from above
                        "to": "col_multiplied",  # new column name
                        "operator": "*",  # multiply the two columns,
                    },
                    # Since we're trying to act on the default input, we don't need explicitly to specify an input
                }
            ],
        ),
    ]

    # Grab the last result from the pipeline, should be our aggregate_workflow since it should be the last one to run
    tables = []
    async for table in run_pipeline(dataset=dataset, workflows=workflows):
        tables.append(table)
    pipeline_result = tables[-1]

    if pipeline_result.result is not None:
        # Should look something like this:
        #     type  aggregated_output
        # 0    A                448
        # 1    B                 90

        # This is because we first in "derive_workflow" we multiply col1 and col2 together, then in "aggregate_workflow" we sum them up by type
        print(pipeline_result.result)
    else:
        print("No results!")


if __name__ == "__main__":
    asyncio.run(run_python())
    asyncio.run(run_with_config())
