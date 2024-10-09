# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to summarize entities."""

from typing import Any

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.operations.snapshot_rows import snapshot_rows
from graphrag.index.operations.summarize_descriptions import (
    summarize_descriptions,
)
from graphrag.index.storage import PipelineStorage


async def create_summarized_entities(
    entities: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    summarization_strategy: dict[str, Any] | None = None,
    num_threads: int = 4,
    graphml_snapshot_enabled: bool = False,
) -> pd.DataFrame:
    """All the steps to summarize entities."""
    summarized = await summarize_descriptions(
        entities,
        callbacks,
        cache,
        column="entity_graph",
        to="entity_graph",
        strategy=summarization_strategy,
        num_threads=num_threads,
    )

    if graphml_snapshot_enabled:
        await snapshot_rows(
            summarized,
            column="entity_graph",
            base_name="summarized_graph",
            storage=storage,
            formats=[{"format": "text", "extension": "graphml"}],
        )

    return summarized
