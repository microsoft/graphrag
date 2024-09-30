# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to extract and format covariates."""

from typing import Any, cast
from uuid import uuid4

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
from graphrag.index.verbs.entities.extraction.entity_extract import entity_extract_df

@verb(name="create_base_extracted_entities", treats_input_tables_as_immutable=True)
async def create_base_extracted_entities(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    column: str,
    id_column: str,
    strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    **kwargs: dict,
) -> VerbResult:
    """All the steps to extract and format covariates."""
    source = cast(pd.DataFrame, input.get_input())

    entity_graph = await entity_extract_df(
        source,
        cache,
        callbacks,
        column=column,
        id_column=id_column,
        strategy=strategy,
        async_mode=async_mode,
        entity_types=entity_types,
        to="entities",
        graph_to="entity_graph",
        **kwargs,
    )
    
    return create_verb_result(
        cast(
            Table,
            entity_graph
        )
    )
