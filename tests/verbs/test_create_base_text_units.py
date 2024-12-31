# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from datashaper import NoopVerbCallbacks

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_base_text_units import run_workflow

from .util import (
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_base_text_units():
    expected = load_test_table("create_base_text_units")

    context = await create_test_context()

    config = create_graphrag_config()
    # test data was created with 4o, so we need to match the encoding for chunks to be identical
    config.chunks.encoding_model = "o200k_base"

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await context.runtime_storage.get("create_base_text_units")

    compare_outputs(actual, expected)


async def test_create_base_text_units_with_snapshot():
    context = await create_test_context()

    config = create_graphrag_config()
    # test data was created with 4o, so we need to match the encoding for chunks to be identical
    config.chunks.encoding_model = "o200k_base"
    config.snapshots.transient = True

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    assert context.storage.keys() == ["create_base_text_units.parquet"], (
        "Text unit snapshot keys differ"
    )
