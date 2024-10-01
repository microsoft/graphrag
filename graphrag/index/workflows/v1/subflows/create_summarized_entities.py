# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final documents."""

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
from graphrag.index.storage import PipelineStorage
from graphrag.index.verbs.entities.summarize.description_summarize import (
    summarize_descriptions_df,
)
from graphrag.index.verbs.snapshot_rows import snapshot_rows_df


@verb(
    name="create_summarized_entities",
    treats_input_tables_as_immutable=True,
)
async def create_summarized_entities(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    strategy: dict[str, Any] | None = None,
    num_threads: int = 4,
    graphml_snapshot_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final documents."""
    source = cast(pd.DataFrame, input.get_input())

    summarized = await summarize_descriptions_df(
        source,
        cache,
        callbacks,
        column="entity_graph",
        to="entity_graph",
        strategy=strategy,
        num_threads=num_threads,
    )

    if graphml_snapshot_enabled:
        await snapshot_rows_df(
            summarized,
            column="entity_graph",
            base_name="summarized_graph",
            storage=storage,
            formats=[{"format": "text", "extension": "graphml"}],
        )

    return create_verb_result(cast(Table, summarized))
