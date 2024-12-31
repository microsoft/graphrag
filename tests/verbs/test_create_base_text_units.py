# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from datashaper import NoopVerbCallbacks

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.create_base_text_units import run_workflow

from .util import (
    compare_outputs,
    load_test_table,
)


async def test_create_base_text_units():
    documents = load_test_table("source_documents")
    expected = load_test_table("create_base_text_units")

    config = create_graphrag_config()
    context = create_run_context(None, None, None)

    # test data was created with 4o, so we need to match the encoding for chunks to be identical
    config.chunks.encoding_model = "o200k_base"

    await context.runtime_storage.set("input", documents)

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await context.runtime_storage.get("base_text_units")

    compare_outputs(actual, expected)


async def test_create_base_text_units_with_snapshot():
    documents = load_test_table("source_documents")

    context = create_run_context(None, None, None)
    config = create_graphrag_config()

    # test data was created with 4o, so we need to match the encoding for chunks to be identical
    config.chunks.encoding_model = "o200k_base"
    config.snapshots.transient = True

    await context.runtime_storage.set("input", documents)

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    assert context.storage.keys() == ["create_base_text_units.parquet"], (
        "Text unit snapshot keys differ"
    )
