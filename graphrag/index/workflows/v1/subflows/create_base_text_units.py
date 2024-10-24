# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform base text_units."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.flows.create_base_text_units import (
    create_base_text_units as create_base_text_units_flow,
)
from graphrag.index.storage import PipelineStorage


@verb(name="create_base_text_units", treats_input_tables_as_immutable=True)
async def create_base_text_units(
    input: VerbInput,
    callbacks: VerbCallbacks,
    runtime_storage: PipelineStorage,
    chunk_column_name: str,
    n_tokens_column_name: str,
    chunk_by_columns: list[str],
    chunk_strategy: dict[str, Any] | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform base text_units."""
    source = cast(pd.DataFrame, input.get_input())

    output = create_base_text_units_flow(
        source,
        callbacks,
        chunk_column_name,
        n_tokens_column_name,
        chunk_by_columns,
        chunk_strategy=chunk_strategy,
    )

    await runtime_storage.set("base_text_units", output)

    return create_verb_result(
        cast(
            Table,
            pd.DataFrame(),
        )
    )
