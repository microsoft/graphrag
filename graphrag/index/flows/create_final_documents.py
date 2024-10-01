# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final documents."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.verbs.text.embed.text_embed import text_embed_df


async def create_final_documents(
    documents: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    text_embed: dict | None = None,
) -> pd.DataFrame:
    """All the steps to transform final documents."""
    documents.rename(columns={"text_units": "text_unit_ids"}, inplace=True)

    if text_embed:
        documents["raw_content_embedding"] = await text_embed_df(
            documents,
            callbacks,
            cache,
            column="raw_content",
            strategy=text_embed["strategy"],
        )

    return documents
