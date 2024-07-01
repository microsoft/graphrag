# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

import pandas as pd

from examples.custom_set_of_available_workflows.custom_workflow_definitions import (
    custom_workflows,
)
from graphrag.index import run_pipeline, run_pipeline_with_config
from graphrag.index.config import PipelineWorkflowReference

sample_data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../_sample_data/"
)

# our fake dataset
dataset = pd.DataFrame([{"col1": 2, "col2": 4}, {"col1": 5, "col2": 10}])


async def run_with_config():
    """Run a pipeline with a config file"""
    # load pipeline.yml in this directory
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "./pipeline.yml"
    )

    # Grab the last result from the pipeline, should be our entity extraction
    tables = []
    async for table in run_pipeline_with_config(
        config_or_path=config_path,
        dataset=dataset,
        additional_workflows=custom_workflows,
    ):
        tables.append(table)
    pipeline_result = tables[-1]

    if pipeline_result.result is not None:
        # Should look something like this:
        #    col1  col2  col_1_multiplied
        # 0     2     4                 8
        # 1     5    10                50
        print(pipeline_result.result)
    else:
        print("No results!")


async def run_python():
    """Run a pipeline using the python API"""
    # Define the actual workflows to be run, this is identical to the python api
    # but we're defining the workflows to be run via python instead of via a config file
    workflows: list[PipelineWorkflowReference] = [
        # run my_workflow against the dataset, notice we're only using the "my_workflow" workflow
        # and not the "my_unused_workflow" workflow
        PipelineWorkflowReference(
            name="my_workflow",  # should match the name of the workflow in the custom_workflows dict above
            config={  # pass in a config
                # set the derive_output_column to be "col_1_multiplied",  this will be passed to the workflow definition above
                "derive_output_column": "col_1_multiplied"
            },
        ),
    ]

    # Grab the last result from the pipeline, should be our entity extraction
    tables = []
    async for table in run_pipeline(
        workflows, dataset=dataset, additional_workflows=custom_workflows
    ):
        tables.append(table)
    pipeline_result = tables[-1]

    if pipeline_result.result is not None:
        # Should look something like this:
        #    col1  col2  col_1_multiplied
        # 0     2     4                 8
        # 1     5    10                50
        print(pipeline_result.result)
    else:
        print("No results!")


if __name__ == "__main__":
    asyncio.run(run_python())
    asyncio.run(run_with_config())
