# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

import pandas as pd

from graphrag.index import run_pipeline, run_pipeline_with_config
from graphrag.index.config import PipelineWorkflowReference

# our fake dataset
dataset = pd.DataFrame([{"col1": 2, "col2": 4}, {"col1": 5, "col2": 10}])


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
        #    col1  col2  col_multiplied
        # 0     2     4               8
        # 1     5    10              50
        print(pipeline_result.result)
    else:
        print("No results!")


async def run_python():
    """Run a pipeline using the python API"""
    workflows: list[PipelineWorkflowReference] = [
        PipelineWorkflowReference(
            steps=[
                {
                    # built-in verb
                    "verb": "derive",  # https://github.com/microsoft/datashaper/blob/main/python/datashaper/datashaper/verbs/derive.py
                    "args": {
                        "column1": "col1",  # from above
                        "column2": "col2",  # from above
                        "to": "col_multiplied",  # new column name
                        "operator": "*",  # multiply the two columns
                    },
                    # Since we're trying to act on the default input, we don't need explicitly to specify an input
                }
            ]
        ),
    ]

    # Grab the last result from the pipeline, should be our entity extraction
    tables = []
    async for table in run_pipeline(dataset=dataset, workflows=workflows):
        tables.append(table)
    pipeline_result = tables[-1]

    if pipeline_result.result is not None:
        # Should look something like this:
        #    col1  col2  col_multiplied
        # 0     2     4               8
        # 1     5    10              50
        print(pipeline_result.result)
    else:
        print("No results!")


if __name__ == "__main__":
    asyncio.run(run_with_config())
    asyncio.run(run_python())
