# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from datashaper import NoopVerbCallbacks

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.compute_communities import run_workflow

from .util import (
    compare_outputs,
    load_test_table,
)


async def test_compute_communities():
    edges = load_test_table("base_relationship_edges")
    expected = load_test_table("base_communities")

    config = create_graphrag_config()
    context = create_run_context(None, None, None)

    await context.runtime_storage.set("base_relationship_edges", edges)

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await context.runtime_storage.get("base_communities")

    columns = list(expected.columns.values)
    compare_outputs(actual, expected, columns)
    assert len(actual.columns) == len(expected.columns)
