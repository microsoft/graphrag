# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.embeddings import (
    all_embeddings,
)
from graphrag.config.enums import ModelType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.workflows.generate_text_embeddings import (
    run_workflow,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
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

    config = GraphRagConfig(models=DEFAULT_MODEL_CONFIG)  # type: ignore
    llm_settings = config.get_language_model_config(config.embed_text.model_id)
    llm_settings.type = ModelType.MockEmbedding

    config.embed_text.names = list(all_embeddings)
    config.snapshots.embeddings = True

    await run_workflow(config, context)

    parquet_files = context.output_storage.keys()

    for field in all_embeddings:
        assert f"embeddings.{field}.parquet" in parquet_files

    # entity description should always be here, let's assert its format
    entity_description_embeddings = await load_table_from_storage(
        "embeddings.entity_description", context.output_storage
    )

    assert len(entity_description_embeddings.columns) == 2
    assert "id" in entity_description_embeddings.columns
    assert "embedding" in entity_description_embeddings.columns
