# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

from graphrag.index import run_pipeline_with_config


async def main():
    if (
        "EXAMPLE_OPENAI_API_KEY" not in os.environ
        and "OPENAI_API_KEY" not in os.environ
    ):
        msg = "Please set EXAMPLE_OPENAI_API_KEY or OPENAI_API_KEY environment variable to run this example"
        raise Exception(msg)

    # run the pipeline with the config, and override the dataset with the one we just created
    # and grab the last result from the pipeline, should be our entity extraction
    pipeline_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "./pipelines/workflows_and_inputs.yml",
    )

    # run the pipeline with the config, and override the dataset with the one we just created
    # and grab the last result from the pipeline, should be the last workflow that was run (our nodes)
    tables = []
    async for table in run_pipeline_with_config(pipeline_path):
        tables.append(table)
    pipeline_result = tables[-1]

    # The output will contain a list of positioned nodes
    if pipeline_result.result is not None:
        top_nodes = pipeline_result.result.head(10)
        print("pipeline result", top_nodes)
    else:
        print("No results!")


if __name__ == "__main__":
    asyncio.run(main())
