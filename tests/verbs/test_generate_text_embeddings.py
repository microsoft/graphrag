# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from io import BytesIO

import pandas as pd
from datashaper import NoopVerbCallbacks

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.enums import TextEmbeddingTarget
from graphrag.index.config.embeddings import (
    all_embeddings,
)
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.generate_text_embeddings import (
    run_workflow,
)

from .util import (
    load_test_table,
)


async def test_generate_text_embeddings():
    inputs = [
        "create_final_documents",
        "create_final_relationships",
        "create_final_text_units",
        "create_final_entities",
        "create_final_community_reports",
    ]

    context = create_run_context(None, None, None)
    config = create_graphrag_config()

    config.embeddings.strategy = {
        "type": "mock",
    }
    config.embeddings.target = TextEmbeddingTarget.all
    config.snapshots.embeddings = True

    for input in inputs:
        table = load_test_table(input)
        await context.storage.set(f"{input}.parquet", table.to_parquet())

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    parquet_files = context.storage.keys()

    for field in all_embeddings:
        assert f"embeddings.{field}.parquet" in parquet_files

    # entity description should always be here, let's assert its format
    entity_description_embeddings_buffer = BytesIO(
        await context.storage.get(
            "embeddings.entity.description.parquet", as_bytes=True
        )
    )
    entity_description_embeddings = pd.read_parquet(
        entity_description_embeddings_buffer
    )
    assert len(entity_description_embeddings.columns) == 2
    assert "id" in entity_description_embeddings.columns
    assert "embedding" in entity_description_embeddings.columns

    # every other embedding is optional but we've turned them all on, so check a random one
    document_text_embeddings_buffer = BytesIO(
        await context.storage.get("embeddings.document.text.parquet", as_bytes=True)
    )
    document_text_embeddings = pd.read_parquet(document_text_embeddings_buffer)
    assert len(document_text_embeddings.columns) == 2
    assert "id" in document_text_embeddings.columns
    assert "embedding" in document_text_embeddings.columns
