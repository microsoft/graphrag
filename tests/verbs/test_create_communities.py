# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_communities import (
    run_workflow,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_communities():
    expected = load_test_table("communities")

    context = await create_test_context(
        storage=[
            "entities",
            "relationships",
        ],
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage("communities", context.storage)

    assert "period" in expected.columns
    columns = list(expected.columns.values)
    columns.remove("period")
    compare_outputs(
        actual,
        expected,
        columns=columns,
    )
