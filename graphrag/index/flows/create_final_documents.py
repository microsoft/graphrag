# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final documents."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.operations.embed_text.embed_text import embed_text


async def create_final_documents(
    documents: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    raw_content_text_embed: dict | None = None,
) -> pd.DataFrame:
    """All the steps to transform final documents."""
    documents.rename(columns={"text_units": "text_unit_ids"}, inplace=True)

    if raw_content_text_embed:
        documents["raw_content_embedding"] = await embed_text(
            documents,
            callbacks,
            cache,
            column="raw_content",
            strategy=raw_content_text_embed["strategy"],
        )

    return documents
