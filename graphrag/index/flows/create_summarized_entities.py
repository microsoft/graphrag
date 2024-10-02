# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to summarize entities."""

from typing import Any

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.storage import PipelineStorage
from graphrag.index.verbs.entities.summarize.description_summarize import (
    summarize_descriptions_df,
)
from graphrag.index.verbs.snapshot_rows import snapshot_rows_df


async def create_summarized_entities(
    entities: pd.DataFrame,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    strategy: dict[str, Any] | None = None,
    num_threads: int = 4,
    graphml_snapshot_enabled: bool = False,
) -> pd.DataFrame:
    """All the steps to summarize entities."""
    summarized = await summarize_descriptions_df(
        entities,
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

    return summarized
