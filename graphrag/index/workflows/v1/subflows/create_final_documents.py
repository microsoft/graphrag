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
from graphrag.index.utils.ds_util import get_required_input_table


@verb(
    name="create_final_documents",
    treats_input_tables_as_immutable=True,
)
async def create_final_documents(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    document_attribute_columns: list[str] | None = None,
    raw_content_text_embed: dict | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final documents."""
    source = cast(pd.DataFrame, input.get_input())
    text_units = cast(pd.DataFrame, get_required_input_table(input, "text_units").table)

    output = await create_final_documents_flow(
        source,
        text_units,
        callbacks,
        cache,
        document_attribute_columns=document_attribute_columns,
        raw_content_text_embed=raw_content_text_embed,
    )

    return create_verb_result(cast(Table, output))
