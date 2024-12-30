# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import TYPE_CHECKING, cast

import pandas as pd
from datashaper import (
    DEFAULT_INPUT_NAME,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.config.models.chunking_config import ChunkStrategyType
from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_base_text_units import (
    create_base_text_units,
)
from graphrag.index.operations.snapshot import snapshot
from graphrag.storage.pipeline_storage import PipelineStorage

if TYPE_CHECKING:
    from graphrag.config.models.chunking_config import ChunkingConfig

workflow_name = "create_base_text_units"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for text units.

    ## Dependencies
    (input dataframe)
    """
    chunks = cast("ChunkingConfig", config.get("chunks"))
    group_by_columns = chunks.group_by_columns
    size = chunks.size
    overlap = chunks.overlap
    encoding_model = chunks.encoding_model
    strategy = chunks.strategy

    snapshot_transient = config.get("snapshot_transient", False) or False
    return [
        {
            "verb": workflow_name,
            "args": {
                "group_by_columns": group_by_columns,
                "size": size,
                "overlap": overlap,
                "encoding_model": encoding_model,
                "strategy": strategy,
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
    group_by_columns: list[str],
    size: int,
    overlap: int,
    encoding_model: str,
    strategy: ChunkStrategyType,
    snapshot_transient_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform base text_units."""
    source = cast("pd.DataFrame", input.get_input())

    output = create_base_text_units(
        source,
        callbacks,
        group_by_columns,
        size,
        overlap,
        encoding_model,
        strategy=strategy,
    )

    await runtime_storage.set("base_text_units", output)

    if snapshot_transient_enabled:
        await snapshot(
            output,
            name="create_base_text_units",
            storage=storage,
            formats=["parquet"],
        )

    return create_verb_result(
        cast(
            "Table",
            pd.DataFrame(),
        )
    )
