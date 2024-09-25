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
from graphrag.index.verbs.text.embed.text_embed import text_embed_df


@verb(
    name="create_final_documents",
    treats_input_tables_as_immutable=True,
)
async def create_final_documents(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    text_embed: dict,
    skip_embedding: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final documents."""
    source = cast(pd.DataFrame, input.get_input())

    source.rename(columns={"text_units": "text_unit_ids"}, inplace=True)

    if not skip_embedding:
        source = await text_embed_df(
            source,
            callbacks,
            cache,
            column="raw_content",
            strategy=text_embed["strategy"],
            to="raw_content_embedding",
        )

    return create_verb_result(cast(Table, source))
