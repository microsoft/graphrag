# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Verb test for the update_text_embeddings workflow."""

from unittest.mock import patch

from graphrag.config.embeddings import all_embeddings
from graphrag.index.workflows.update_text_embeddings import (
    run_workflow,
)

from tests.unit.config.utils import get_default_graphrag_config

from .util import create_test_context


async def test_update_text_embeddings():
    """Verify update_text_embeddings produces embedding tables.

    Mocks get_update_table_providers to return the test context's
    output_table_provider, simulating the merged tables written by
    upstream update workflows.
    """
    context = await create_test_context(
        storage=[
            "documents",
            "relationships",
            "text_units",
            "entities",
            "community_reports",
        ]
    )
    context.state["update_timestamp"] = "20260220-000000"

    config = get_default_graphrag_config()
    llm_settings = config.get_embedding_model_config(
        config.embed_text.embedding_model_id
    )
    llm_settings.type = "mock"
    llm_settings.mock_responses = [1.0] * 3072

    config.embed_text.names = list(all_embeddings)
    config.snapshots.embeddings = True

    with patch(
        "graphrag.index.workflows.update_text_embeddings.get_update_table_providers",
    ) as mock_providers:
        mock_providers.return_value = (
            context.output_table_provider,
            None,
            None,
        )
        await run_workflow(config, context)

    parquet_files = context.output_storage.keys()
    for field in all_embeddings:
        assert f"embeddings.{field}.parquet" in parquet_files

    entity_embeddings = await context.output_table_provider.read_dataframe(
        "embeddings.entity_description"
    )
    assert len(entity_embeddings.columns) == 2
    assert "id" in entity_embeddings.columns
    assert "embedding" in entity_embeddings.columns
