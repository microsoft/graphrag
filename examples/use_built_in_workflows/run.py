# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

from graphrag.index import run_pipeline, run_pipeline_with_config
from graphrag.index.config import PipelineCSVInputConfig, PipelineWorkflowReference
from graphrag.index.input import load_input

sample_data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../_sample_data/"
)

# Load our dataset once
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

    if pipeline_result.result is not None:
        # The output of this should match the run_python() example
        first_result = pipeline_result.result.head(1)
        print(f"level: {first_result['level'][0]}")
        print(f"embeddings: {first_result['embeddings'][0]}")
        print(f"entity_graph_positions: {first_result['node_positions'][0]}")
    else:
        print("No results!")


async def run_python():
    # We're cheap, and this is an example, lets just do 10
    dataset = shared_dataset.head(10)

    workflows: list[PipelineWorkflowReference] = [
        # This workflow reference here is only necessary
        # because we want to customize the entity_extraction workflow is configured
        # otherwise, it can be omitted, but you're stuck with the default configuration for entity_extraction
        PipelineWorkflowReference(
            name="entity_extraction",
            config={
                "entity_extract": {
                    "strategy": {
                        "type": "nltk",
                    }
                }
            },
        ),
        PipelineWorkflowReference(
            name="entity_graph",
            config={
                "cluster_graph": {"strategy": {"type": "leiden"}},
                "embed_graph": {
                    "strategy": {
                        "type": "node2vec",
                        "num_walks": 10,
                        "walk_length": 40,
                        "window_size": 2,
                        "iterations": 3,
                        "random_seed": 597832,
                    }
                },
                "layout_graph": {
                    "strategy": {
                        "type": "umap",
                    },
                },
            },
        ),
    ]

    # Grab the last result from the pipeline, should be our entity extraction
    tables = []
    async for table in run_pipeline(dataset=dataset, workflows=workflows):
        tables.append(table)
    pipeline_result = tables[-1]

    # The output will contain entity graphs per hierarchical level, with embeddings per entity
    if pipeline_result.result is not None:
        first_result = pipeline_result.result.head(1)
        print(f"level: {first_result['level'][0]}")
        print(f"embeddings: {first_result['embeddings'][0]}")
        print(f"entity_graph_positions: {first_result['node_positions'][0]}")
    else:
        print("No results!")


if __name__ == "__main__":
    asyncio.run(run_python())
    asyncio.run(run_with_config())
