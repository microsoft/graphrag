# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to summarize entities."""

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
from graphrag.index.flows.create_summarized_entities import (
    create_summarized_entities as create_summarized_entities_flow,
)
from graphrag.index.storage import PipelineStorage


@verb(
    name="create_summarized_entities",
    treats_input_tables_as_immutable=True,
)
async def create_summarized_entities(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    column: str,
    id_column: str,
    extraction_strategy: dict[str, Any] | None,
    extraction_num_threads: int = 4,
    extraction_async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    node_merge_config: dict[str, Any] | None = None,
    edge_merge_config: dict[str, Any] | None = None,
    summarization_strategy: dict[str, Any] | None = None,
    summarization_num_threads: int = 4,
    graphml_snapshot_enabled: bool = False,
    raw_entity_snapshot_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to summarize entities."""
    source = cast(pd.DataFrame, input.get_input())

    output = await create_summarized_entities_flow(
        source,
        callbacks,
        cache,
        storage,
        column,
        id_column,
        extraction_strategy=extraction_strategy,
        extraction_num_threads=extraction_num_threads,
        extraction_async_mode=extraction_async_mode,
        entity_types=entity_types,
        node_merge_config=node_merge_config,
        edge_merge_config=edge_merge_config,
        summarization_strategy=summarization_strategy,
        summarization_num_threads=summarization_num_threads,
        graphml_snapshot_enabled=graphml_snapshot_enabled,
        raw_entity_snapshot_enabled=raw_entity_snapshot_enabled,
    )

    return create_verb_result(cast(Table, output))
