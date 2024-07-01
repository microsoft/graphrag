# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

from graphrag.index import run_pipeline_with_config
from graphrag.index.config import PipelineCSVInputConfig
from graphrag.index.input import load_input

sample_data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../_sample_data/"
)


async def main():
    if (
        "EXAMPLE_OPENAI_API_KEY" not in os.environ
        and "OPENAI_API_KEY" not in os.environ
    ):
        msg = "Please set EXAMPLE_OPENAI_API_KEY or OPENAI_API_KEY environment variable to run this example"
        raise Exception(msg)

    dataset = await load_input(
        PipelineCSVInputConfig(
            file_pattern=".*\\.csv$",
            base_dir=sample_data_dir,
            source_column="author",
            text_column="message",
            timestamp_column="date(yyyyMMddHHmmss)",
            timestamp_format="%Y%m%d%H%M%S",
            title_column="message",
        ),
    )

    # We're cheap, and this is an example, lets just do 10
    dataset = dataset.head(10)

    # run the pipeline with the config, and override the dataset with the one we just created
    # and grab the last result from the pipeline, should be the last workflow that was run (our nodes)
    pipeline_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "./pipelines/workflows_only.yml"
    )
    tables = []
    async for table in run_pipeline_with_config(pipeline_path, dataset=dataset):
        tables.append(table)
    pipeline_result = tables[-1]

    # The output will contain a list of positioned nodes
    if pipeline_result.result is not None:
        top_nodes = pipeline_result.result.head(10)
        print(
            "pipeline result\ncols: ", pipeline_result.result.columns, "\n", top_nodes
        )
    else:
        print("No results!")


if __name__ == "__main__":
    asyncio.run(main())
