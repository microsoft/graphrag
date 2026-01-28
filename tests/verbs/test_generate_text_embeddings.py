# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.embeddings import (
    all_embeddings,
)
from graphrag.index.workflows.generate_text_embeddings import (
    run_workflow,
)

from tests.unit.config.utils import get_default_graphrag_config

from .util import (
    create_test_context,
)


async def test_generate_text_embeddings():
    context = await create_test_context(
        storage=[
            "documents",
            "relationships",
            "text_units",
            "entities",
            "community_reports",
        ]
    )

    config = get_default_graphrag_config()
    llm_settings = config.get_embedding_model_config(
        config.embed_text.embedding_model_id
    )
    llm_settings.type = "mock"
    llm_settings.mock_responses = [1.0] * 3072

    config.embed_text.names = list(all_embeddings)
    config.snapshots.embeddings = True

    await run_workflow(config, context)

    parquet_files = context.output_storage.keys()

    for field in all_embeddings:
        assert f"embeddings.{field}.parquet" in parquet_files

    # entity description should always be here, let's assert its format
    entity_description_embeddings = await context.output_table_provider.read_dataframe(
        "embeddings.entity_description"
    )

    assert len(entity_description_embeddings.columns) == 2
    assert "id" in entity_description_embeddings.columns
    assert "embedding" in entity_description_embeddings.columns
