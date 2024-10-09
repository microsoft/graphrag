# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to summarize entities."""

from typing import Any, cast

import pandas as pd
from datashaper import (
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
    summarization_strategy: dict[str, Any] | None = None,
    num_threads: int = 4,
    graphml_snapshot_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to summarize entities."""
    source = cast(pd.DataFrame, input.get_input())

    output = await create_summarized_entities_flow(
        source,
        callbacks,
        cache,
        storage,
        summarization_strategy,
        num_threads=num_threads,
        graphml_snapshot_enabled=graphml_snapshot_enabled,
    )

    return create_verb_result(cast(Table, output))
