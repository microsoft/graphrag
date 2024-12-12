# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    DEFAULT_INPUT_NAME,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_base_text_units import (
    create_base_text_units,
)
from graphrag.storage.pipeline_storage import PipelineStorage

workflow_name = "create_base_text_units"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for text units.

    ## Dependencies
    (input dataframe)
    """
    chunk_by_columns = config.get("chunk_by", []) or []
    text_chunk_config = config.get("text_chunk", {})
    chunk_strategy = text_chunk_config.get("strategy")

    snapshot_transient = config.get("snapshot_transient", False) or False
    return [
        {
            "verb": workflow_name,
            "args": {
                "chunk_by_columns": chunk_by_columns,
                "chunk_strategy": chunk_strategy,
                "snapshot_transient_enabled": snapshot_transient,
            },
            "input": {"source": DEFAULT_INPUT_NAME},
        },
    ]


@verb(name=workflow_name, treats_input_tables_as_immutable=True)
async def workflow(
    input: VerbInput,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    runtime_storage: PipelineStorage,
    chunk_by_columns: list[str],
    chunk_strategy: dict[str, Any] | None = None,
    snapshot_transient_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform base text_units."""
    source = cast("pd.DataFrame", input.get_input())

    output = await create_base_text_units(
        source,
        callbacks,
        storage,
        chunk_by_columns,
        chunk_strategy=chunk_strategy,
        snapshot_transient_enabled=snapshot_transient_enabled,
    )

    await runtime_storage.set("base_text_units", output)

    return create_verb_result(
        cast(
            "Table",
            pd.DataFrame(),
        )
    )
