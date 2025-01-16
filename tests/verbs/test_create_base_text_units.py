# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_base_text_units import run_workflow, workflow_name
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_base_text_units():
    expected = load_test_table(workflow_name)

    context = await create_test_context()

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    # test data was created with 4o, so we need to match the encoding for chunks to be identical
    config.chunks.encoding_model = "o200k_base"

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage(workflow_name, context.storage)

    compare_outputs(actual, expected)
