# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from datashaper import NoopVerbCallbacks

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.create_final_documents import (
    run_workflow,
    workflow_name,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    compare_outputs,
    load_test_table,
)


async def test_create_final_documents():
    documents = load_test_table("source_documents")
    base_text_units = load_test_table("create_base_text_units")
    expected = load_test_table(workflow_name)

    config = create_graphrag_config()
    context = create_run_context(None, None, None)

    await context.runtime_storage.set("input", documents)
    await context.runtime_storage.set("base_text_units", base_text_units)

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await load_table_from_storage(f"{workflow_name}.parquet", context.storage)

    compare_outputs(actual, expected)


async def test_create_final_documents_with_attribute_columns():
    documents = load_test_table("source_documents")
    base_text_units = load_test_table("create_base_text_units")
    expected = load_test_table(workflow_name)

    config = create_graphrag_config()
    context = create_run_context(None, None, None)

    config.input.document_attribute_columns = ["title"]

    await context.runtime_storage.set("input", documents)
    await context.runtime_storage.set("base_text_units", base_text_units)

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await load_table_from_storage(f"{workflow_name}.parquet", context.storage)

    # we should have dropped "title" and added "attributes"
    # our test dataframe does not have attributes, so we'll assert without it
    # and separately confirm it is in the output
    compare_outputs(
        actual, expected, columns=["id", "human_readable_id", "text", "text_unit_ids"]
    )
    assert len(actual.columns) == 5
    assert "title" not in actual.columns
    assert "attributes" in actual.columns
