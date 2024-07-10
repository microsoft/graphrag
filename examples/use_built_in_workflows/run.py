
# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from graphrag.index.workflows import WorkflowDefinitions

import asyncio
import os
import pandas as pd

from graphrag.index import run_pipeline, run_pipeline_with_config, PipelineWorkflowStep, PipelineWorkflowConfig
from graphrag.index.config import PipelineCSVInputConfig, PipelineWorkflowReference
from graphrag.index.input import load_input

# Load our dataset once
shared_dataset = pd.DataFrame([{"author": "aufsnn",
                                "message": "Apple Inc. is an American multinational technology company headquartered in Cupertino, California. Tim Cook is the CEO of Apple.",
                                "date(yyyyMMddHHmmss)": "20240709182511"
                                }])


def build_entity_extraction_steps(
        config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    entity_extraction_config = config.get("entity_extract", {})

    return [
        {
            "verb": "entity_extract",
            "args": {
                **entity_extraction_config,

                "column": "message",
                "id_column": "author",
                "async_mode": "asyncio",
                "to": "entities",
                "graph_to": "entity_graph",
            },
        },

    ]


def build_entity_graph_steps(
        config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    clustering_config = config.get(
        "cluster_graph",
        {"strategy": {"type": "leiden"}},
    )
    embed_graph_config = config.get(
        "embed_graph",
        {
            "strategy": {
                "type": "node2vec",
                "num_walks": config.get("embed_num_walks", 10),
                "walk_length": config.get("embed_walk_length", 40),
                "window_size": config.get("embed_window_size", 2),
                "iterations": config.get("embed_iterations", 3),
                "random_seed": config.get("embed_random_seed", 86),
            }
        },
    )

    layout_graph_config = config.get(
        "layout_graph",
        {
            "strategy": {
                "type": "umap",
            },
        },
    )

    return [
        {
            "id": "custom_graph_nodes",
            "verb": "cluster_graph",
            "args": {
                **clustering_config,
                "column": "entity_graph",
                "to": "clustered_graph",
                "level_to": "level",
            },
            "input": ({"source": "workflow:entity_extraction"}),
        },
        {
            "id": "custom_embed_nodes",
            "verb": "embed_graph",
            "args": {

                "column": "clustered_graph",
                "to": "embeddings",
                **embed_graph_config,
            },

            "input": {"source": "custom_graph_nodes"},
        },
        {
            "id": "custom_laid_out_entity_graph",
            "verb": "layout_graph",
            "args": {
                "embeddings_column": "embeddings",
                "graph_column": "clustered_graph",
                "to": "node_positions",
                "graph_to": "positioned_graph",
                **layout_graph_config,
            },

            "input": {"source": "custom_embed_nodes", "others": ["custom_graph_nodes"]},
        },
    ]


custom_workflows: WorkflowDefinitions = {
    "entity_extraction": build_entity_extraction_steps,
    "entity_graph": build_entity_graph_steps
}


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
            config_or_path=config_path, dataset=dataset, additional_workflows=custom_workflows
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
    async for table in run_pipeline(dataset=dataset, workflows=workflows, additional_workflows=custom_workflows):
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
