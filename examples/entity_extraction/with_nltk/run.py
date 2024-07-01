# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

from graphrag.index import run_pipeline, run_pipeline_with_config
from graphrag.index.config import PipelineCSVInputConfig, PipelineWorkflowReference
from graphrag.index.input import load_input

sample_data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../../_sample_data/"
)
shared_dataset = asyncio.run(
    load_input(
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
)


async def run_with_config():
    """Run a pipeline with a config file"""
    # We're cheap, and this is an example, lets just do 10
    dataset = shared_dataset.head(10)

    # load pipeline.yml in this directory
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "./pipeline.yml"
    )

    # Grab the last result from the pipeline, should be our entity extraction
    tables = []
    async for table in run_pipeline_with_config(
        config_or_path=config_path, dataset=dataset
    ):
        tables.append(table)
    pipeline_result = tables[-1]

    # Print the entities.  This will be a row for each text unit, each with a list of entities
    if pipeline_result.result is not None:
        print(pipeline_result.result["entities"].to_list())
    else:
        print("No results!")


async def run_python():
    dataset = shared_dataset.head(10)

    workflows: list[PipelineWorkflowReference] = [
        PipelineWorkflowReference(
            name="entity_extraction",
            config={"entity_extract": {"strategy": {"type": "nltk"}}},
        )
    ]

    # Grab the last result from the pipeline, should be our entity extraction
    tables = []
    async for table in run_pipeline(dataset=dataset, workflows=workflows):
        tables.append(table)
    pipeline_result = tables[-1]

    # Print the entities.  This will be a row for each text unit, each with a list of entities
    if pipeline_result.result is not None:
        print(pipeline_result.result["entities"].to_list())
    else:
        print("No results!")


if __name__ == "__main__":
    asyncio.run(run_python())
    asyncio.run(run_with_config())
