# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from io import BytesIO

import pandas as pd

from graphrag.index.config.embeddings import (
    all_embeddings,
)
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.generate_text_embeddings import (
    build_steps,
    workflow_name,
)

from .util import (
    get_config_for_workflow,
    get_workflow_output,
    load_input_tables,
)


async def test_generate_text_embeddings():
    input_tables = load_input_tables(
        inputs=[
            "workflow:create_final_documents",
            "workflow:create_final_relationships",
            "workflow:create_final_text_units",
            "workflow:create_final_entities",
            "workflow:create_final_community_reports",
        ]
    )
    context = create_run_context(None, None, None)

    config = get_config_for_workflow(workflow_name)

    config["text_embed"]["strategy"]["type"] = "mock"
    config["snapshot_embeddings"] = True

    config["embedded_fields"] = all_embeddings

    steps = build_steps(config)

    await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context,
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
