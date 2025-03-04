# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_base_text_units import run_workflow
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    compare_outputs,
    create_test_context,
    load_test_table,
    update_document_metadata,
)


async def test_create_base_text_units():
    expected = load_test_table("text_units")

    context = await create_test_context()

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})

    await run_workflow(config, context)

    actual = await load_table_from_storage("text_units", context.storage)

    compare_outputs(actual, expected, columns=["text", "document_ids", "n_tokens"])


async def test_create_base_text_units_metadata():
    expected = load_test_table("text_units_metadata")

    context = await create_test_context()

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    # test data was created with 4o, so we need to match the encoding for chunks to be identical
    config.chunks.encoding_model = "o200k_base"
    config.input.metadata = ["title"]
    config.chunks.prepend_metadata = True

    await update_document_metadata(config.input.metadata, context)

    await run_workflow(config, context)

    actual = await load_table_from_storage("text_units", context.storage)
    compare_outputs(actual, expected)


async def test_create_base_text_units_metadata_included_in_chunk():
    expected = load_test_table("text_units_metadata_included_chunk")

    context = await create_test_context()

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    # test data was created with 4o, so we need to match the encoding for chunks to be identical
    config.chunks.encoding_model = "o200k_base"
    config.input.metadata = ["title"]
    config.chunks.prepend_metadata = True
    config.chunks.chunk_size_includes_metadata = True

    await update_document_metadata(config.input.metadata, context)

    await run_workflow(config, context)

    actual = await load_table_from_storage("text_units", context.storage)
    # only check the columns from the base workflow - our expected table is the final and will have more
    compare_outputs(actual, expected, columns=["text", "document_ids", "n_tokens"])
