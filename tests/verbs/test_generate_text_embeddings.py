# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.embeddings import (
    all_embeddings,
)
from graphrag.config.enums import ModelType
from graphrag.index.operations.embed_text.embed_text import TextEmbedStrategyType
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

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    llm_settings = config.get_language_model_config(
        config.embed_text.model_id
    ).model_dump()
    llm_settings["type"] = ModelType.MockEmbedding

    config.embed_text.strategy = {
        "type": TextEmbedStrategyType.openai,
        "llm": llm_settings,
    }
    config.embed_text.names = list(all_embeddings)
    config.snapshots.embeddings = True

    await run_workflow(config, context)

    parquet_files = context.storage.keys()

    for field in all_embeddings:
        assert f"embeddings.{field}.parquet" in parquet_files

    # entity description should always be here, let's assert its format
    entity_description_embeddings = await load_table_from_storage(
        "embeddings.entity.description", context.storage
    )

    assert len(entity_description_embeddings.columns) == 2
    assert "id" in entity_description_embeddings.columns
    assert "embedding" in entity_description_embeddings.columns

    # every other embedding is optional but we've turned them all on, so check a random one
    document_text_embeddings = await load_table_from_storage(
        "embeddings.document.text", context.storage
    )

    assert len(document_text_embeddings.columns) == 2
    assert "id" in document_text_embeddings.columns
    assert "embedding" in document_text_embeddings.columns
