# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import Any, cast

import pandas as pd
from datashaper import (
    Table,
    VerbInput,
    VerbResult,
    create_verb_result,
)

from graphrag.index.config import PipelineWorkflowReference
from graphrag.index.run import run_pipeline
from graphrag.index.storage import MemoryPipelineStorage, PipelineStorage


async def mock_verb(
    input: VerbInput, storage: PipelineStorage, **_kwargs
) -> VerbResult:
    source = cast(pd.DataFrame, input.get_input())

    output = source[["id"]]

    await storage.set("mock_write", source[["id"]])

    return create_verb_result(
        cast(
            Table,
            output,
        )
    )


async def mock_no_return_verb(
    input: VerbInput, storage: PipelineStorage, **_kwargs
) -> VerbResult:
    source = cast(pd.DataFrame, input.get_input())

    # write some outputs to storage independent of the return
    await storage.set("empty_write", source[["name"]])

    return create_verb_result(
        cast(
            Table,
            pd.DataFrame(),
        )
    )


async def test_normal_result_emits_parquet():
    mock_verbs: Any = {"mock_verb": mock_verb}
    mock_workflows: Any = {
        "mock_workflow": lambda _x: [
            {
                "verb": "mock_verb",
                "args": {
                    "column": "test",
                },
            }
        ]
    }
    workflows = [
        PipelineWorkflowReference(
            name="mock_workflow",
            config=None,
        )
    ]
    dataset = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
    storage = MemoryPipelineStorage()
    pipeline_result = [
        gen
        async for gen in run_pipeline(
            workflows,
            dataset,
            storage=storage,
            additional_workflows=mock_workflows,
            additional_verbs=mock_verbs,
        )
    ]

    assert len(pipeline_result) == 1
    assert (
        storage.keys() == ["stats.json", "mock_write", "mock_workflow.parquet"]
    ), "Mock workflow output should be written to storage by the emitter when there is a non-empty data frame"


async def test_empty_result_does_not_emit_parquet():
    mock_verbs: Any = {"mock_no_return_verb": mock_no_return_verb}
    mock_workflows: Any = {
        "mock_workflow": lambda _x: [
            {
                "verb": "mock_no_return_verb",
                "args": {
                    "column": "test",
                },
            }
        ]
    }
    workflows = [
        PipelineWorkflowReference(
            name="mock_workflow",
            config=None,
        )
    ]
    dataset = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
    storage = MemoryPipelineStorage()
    pipeline_result = [
        gen
        async for gen in run_pipeline(
            workflows,
            dataset,
            storage=storage,
            additional_workflows=mock_workflows,
            additional_verbs=mock_verbs,
        )
    ]

    assert len(pipeline_result) == 1
    assert storage.keys() == [
        "stats.json",
        "empty_write",
    ], "Mock workflow output should not be written to storage by the emitter"
