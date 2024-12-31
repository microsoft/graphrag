# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from datashaper import NoopVerbCallbacks

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_final_entities import (
    run_workflow,
    workflow_name,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_final_entities():
    expected = load_test_table(workflow_name)

    context = await create_test_context(
        runtime_storage=["base_entity_nodes"],
    )

    config = create_graphrag_config()

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await load_table_from_storage(f"{workflow_name}.parquet", context.storage)

    compare_outputs(actual, expected)
    assert len(actual.columns) == len(expected.columns)
