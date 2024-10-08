# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

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
from graphrag.index.flows.create_final_entities import (
    create_final_entities as create_final_entities_flow,
)


@verb(
    name="create_final_entities",
    treats_input_tables_as_immutable=True,
)
async def create_final_entities(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    name_text_embed: dict,
    description_text_embed: dict,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final entities."""
    source = cast(pd.DataFrame, input.get_input())

    output = await create_final_entities_flow(
        source,
        callbacks,
        cache,
        name_text_embed,
        description_text_embed,
    )

    return create_verb_result(cast(Table, output))
