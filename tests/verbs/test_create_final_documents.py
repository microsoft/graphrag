# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_final_documents import (
    run_workflow,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    compare_outputs,
    create_test_context,
    load_test_table,
    update_document_metadata,
)


async def test_create_final_documents():
    expected = load_test_table("documents")

    context = await create_test_context(
        storage=["text_units"],
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage("documents", context.storage)

    compare_outputs(actual, expected)


async def test_create_final_documents_with_metadata_column():
    context = await create_test_context(
        storage=["text_units"],
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    config.input.metadata = ["title"]

    # simulate the metadata construction during initial input loading
    await update_document_metadata(config.input.metadata, context)

    expected = await load_table_from_storage("documents", context.storage)

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage("documents", context.storage)

    # our test dataframe does not have metadata, so we'll assert without it
    # and separately confirm it is in the output
    compare_outputs(
        actual, expected, columns=["id", "human_readable_id", "text", "metadata"]
    )
    assert len(actual.columns) == 7
    assert "title" in actual.columns
    assert "text_unit_ids" in actual.columns
    assert "metadata" in actual.columns
