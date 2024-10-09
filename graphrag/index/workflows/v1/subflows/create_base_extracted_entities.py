# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to extract and format base entities."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.cache import PipelineCache
from graphrag.index.flows.create_base_extracted_entities import (
    create_base_extracted_entities as create_base_extracted_entities_flow,
)
from graphrag.index.storage import PipelineStorage


@verb(name="create_base_extracted_entities", treats_input_tables_as_immutable=True)
async def create_base_extracted_entities(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    column: str,
    id_column: str,
    nodes: dict[str, Any],
    edges: dict[str, Any],
    extraction_strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    num_threads: int = 4,
    graphml_snapshot_enabled: bool = False,
    raw_entity_snapshot_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to extract and format base entities."""
    source = cast(pd.DataFrame, input.get_input())

    output = await create_base_extracted_entities_flow(
        source,
        callbacks,
        cache,
        storage,
        column,
        id_column,
        nodes,
        edges,
        extraction_strategy,
        async_mode=async_mode,
        entity_types=entity_types,
        graphml_snapshot_enabled=graphml_snapshot_enabled,
        raw_entity_snapshot_enabled=raw_entity_snapshot_enabled,
        num_threads=num_threads,
    )

    return create_verb_result(cast(Table, output))
