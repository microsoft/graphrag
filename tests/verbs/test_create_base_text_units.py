# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_base_text_units import run_workflow
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_base_text_units():
    expected = load_test_table("text_units")

    context = await create_test_context()

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage("text_units", context.storage)

    # only check the columns from the base workflow - our expected table is the final and will have more
    compare_outputs(actual, expected, columns=["text", "document_ids", "n_tokens"])
