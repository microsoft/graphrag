# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

import pandas as pd

from examples.custom_set_of_available_verbs.custom_verb_definitions import custom_verbs
from graphrag.index import run_pipeline, run_pipeline_with_config
from graphrag.index.config import PipelineWorkflowReference

# Our fake dataset
dataset = pd.DataFrame([{"col1": 2, "col2": 4}, {"col1": 5, "col2": 10}])


async def run_with_config():
    """Run a pipeline with a config file"""
    # load pipeline.yml in this directory
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "./pipeline.yml"
    )

    outputs = []
    async for output in run_pipeline_with_config(
        config_or_path=config_path, dataset=dataset
    ):
        outputs.append(output)
    pipeline_result = outputs[-1]

    if pipeline_result.result is not None:
        # Should look something like this, which should be identical to the python example:
        #    col1  col2  col_1_custom
        # 0     2     4  2 - custom verb
        # 1     5    10  5 - custom verb
        print(pipeline_result.result)
    else:
        print("No results!")


async def run_python():
    workflows: list[PipelineWorkflowReference] = [
        PipelineWorkflowReference(
            name="my_workflow",
            steps=[
                {
                    "verb": "str_append",  # should be the key that you pass to the custom_verbs dict below
                    "args": {
                        "source_column": "col1",  # from above
                        "target_column": "col_1_custom",  # new column name,
                        "string_to_append": " - custom verb",  # The string to append to the column
                    },
                    # Since we're trying to act on the default input, we don't need explicitly to specify an input
                }
            ],
        ),
    ]

    # Run the pipeline
    outputs = []
    async for output in run_pipeline(
        dataset=dataset,
        workflows=workflows,
        additional_verbs=custom_verbs,
    ):
        outputs.append(output)

    # Find the result from the workflow we care about
    pipeline_result = next(
        (output for output in outputs if output.workflow == "my_workflow"), None
    )

    if pipeline_result is not None and pipeline_result.result is not None:
        # Should look something like this:
        #    col1  col2     col_1_custom
        # 0     2     4  2 - custom verb
        # 1     5    10  5 - custom verb
        print(pipeline_result.result)
    else:
        print("No results!")


if __name__ == "__main__":
    asyncio.run(run_python())
    asyncio.run(run_with_config())
