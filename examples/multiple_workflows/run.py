# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

from graphrag.index import run_pipeline_with_config
from graphrag.index.config import PipelineCSVInputConfig
from graphrag.index.input import load_input

sample_data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "./../_sample_data/"
)


async def run_with_config():
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
    dataset = dataset.head(2)

    # run the pipeline with the config, and override the dataset with the one we just created
    # and grab the last result from the pipeline, should be the last workflow that was run (our nodes)
    pipeline_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "./pipeline.yml"
    )

    async for result in run_pipeline_with_config(pipeline_path, dataset=dataset):
        print(f"Workflow {result.workflow} result\n: ")
        print(result.result)


if __name__ == "__main__":
    asyncio.run(run_with_config())
