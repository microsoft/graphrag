# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final relationships."""

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
from graphrag.index.flows.create_final_relationships import (
    create_final_relationships as create_final_relationships_flow,
)
from graphrag.index.utils.ds_util import get_required_input_table


@verb(
    name="create_final_relationships",
    treats_input_tables_as_immutable=True,
)
async def create_final_relationships(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    description_text_embed: dict | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final relationships."""
    source = cast(pd.DataFrame, input.get_input())
    nodes = cast(pd.DataFrame, get_required_input_table(input, "nodes").table)

    output = await create_final_relationships_flow(
        source,
        nodes,
        callbacks,
        cache,
        description_text_embed=description_text_embed,
    )

    return create_verb_result(cast(Table, output))
