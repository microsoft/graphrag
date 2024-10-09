# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final documents."""

from typing import cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.cache import PipelineCache
from graphrag.index.flows.create_final_documents import (
    create_final_documents as create_final_documents_flow,
)


@verb(
    name="create_final_documents",
    treats_input_tables_as_immutable=True,
)
async def create_final_documents(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    raw_content_text_embed: dict | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final documents."""
    source = cast(pd.DataFrame, input.get_input())

    output = await create_final_documents_flow(
        source,
        callbacks,
        cache,
        raw_content_text_embed=raw_content_text_embed,
    )

    return create_verb_result(cast(Table, output))
