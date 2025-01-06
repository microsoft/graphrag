# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_final_relationships import (
    run_workflow,
    workflow_name,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_final_relationships():
    expected = load_test_table(workflow_name)

    context = await create_test_context(
        storage=["base_relationship_edges"],
    )

    config = create_graphrag_config()

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage(workflow_name, context.storage)

    assert "id" in expected.columns
    columns = list(expected.columns.values)
    columns.remove("id")
    compare_outputs(actual, expected, columns)
    assert len(actual.columns) == len(expected.columns)
