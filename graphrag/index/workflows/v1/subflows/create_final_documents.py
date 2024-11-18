# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final documents."""

from typing import cast

import pandas as pd
from datashaper import (
    Table,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.flows.create_final_documents import (
    create_final_documents as create_final_documents_flow,
)
from graphrag.index.storage.pipeline_storage import PipelineStorage


@verb(
    name="create_final_documents",
    treats_input_tables_as_immutable=True,
)
async def create_final_documents(
    input: VerbInput,
    runtime_storage: PipelineStorage,
    document_attribute_columns: list[str] | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final documents."""
    source = cast(pd.DataFrame, input.get_input())
    text_units = await runtime_storage.get("base_text_units")

    output = create_final_documents_flow(source, text_units, document_attribute_columns)

    return create_verb_result(cast(Table, output))
