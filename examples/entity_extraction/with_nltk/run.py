# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

from graphrag.index import run_pipeline, run_pipeline_with_config
from graphrag.index.config import PipelineCSVInputConfig, PipelineWorkflowReference
from graphrag.index.input import load_input

# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from graphrag.index.workflows import WorkflowDefinitions
import pandas as pd

custom_workflows: WorkflowDefinitions = {
    "entity_extraction": lambda config: [
        {
            "verb": "entity_extract",
            "args": {
                "column": "message",
                "id_column": "author",
                "async_mode": "asyncio",
                "strategy": config.get('entity_extract', {}).get(
                    "strategy"
                ),
                "to": "entities",
                "graph_to": "entity_graph",
            },
        }
    ]
}

shared_dataset = pd.DataFrame([{"author": "aufsnn",
                                "message": "Apple Inc. is an American multinational technology company headquartered in Cupertino, California. Tim Cook is the CEO of Apple.",
                                "date(yyyyMMddHHmmss)": "20240709182511"
                                },
                               {"author": "dmeck",
                                "message": "hello!",
                                "date(yyyyMMddHHmmss)": "20240709182511"}])


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
            config={"strategy": {"type": "nltk"}},
        )
    ]

    # Grab the last result from the pipeline, should be our entity extraction
    tables = []
    async for table in run_pipeline(dataset=dataset, workflows=workflows, additional_workflows=custom_workflows):
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
