# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_final_documents import (
    run_workflow,
    workflow_name,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_final_documents():
    expected = load_test_table(workflow_name)

    context = await create_test_context(
        storage=["create_base_text_units"],
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage(workflow_name, context.storage)

    compare_outputs(actual, expected)


async def test_create_final_documents_with_attribute_columns():
    expected = load_test_table(workflow_name)

    context = await create_test_context(
        storage=["create_base_text_units"],
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    config.input.document_attribute_columns = ["title"]

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage(workflow_name, context.storage)

    # we should have dropped "title" and added "attributes"
    # our test dataframe does not have attributes, so we'll assert without it
    # and separately confirm it is in the output
    compare_outputs(
        actual, expected, columns=["id", "human_readable_id", "text", "text_unit_ids"]
    )
    assert len(actual.columns) == 5
    assert "title" not in actual.columns
    assert "attributes" in actual.columns
