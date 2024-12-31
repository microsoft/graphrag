# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from datashaper import NoopVerbCallbacks

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.create_final_entities import (
    run_workflow,
    workflow_name,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    compare_outputs,
    load_test_table,
)


async def test_create_final_entities():
    input = load_test_table("base_entity_nodes")
    expected = load_test_table(workflow_name)

    config = create_graphrag_config()
    context = create_run_context(None, None, None)

    await context.runtime_storage.set("base_entity_nodes", input)

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await load_table_from_storage(f"{workflow_name}.parquet", context.storage)

    compare_outputs(actual, expected)
    assert len(actual.columns) == len(expected.columns)
