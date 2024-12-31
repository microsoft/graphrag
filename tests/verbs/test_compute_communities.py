# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from datashaper import NoopVerbCallbacks

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.compute_communities import run_workflow

from .util import (
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_compute_communities():
    expected = load_test_table("base_communities")

    context = await create_test_context(
        runtime_storage=["base_relationship_edges"],
    )

    config = create_graphrag_config()

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await context.runtime_storage.get("base_communities")

    columns = list(expected.columns.values)
    compare_outputs(actual, expected, columns)
    assert len(actual.columns) == len(expected.columns)
