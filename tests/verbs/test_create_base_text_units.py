# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.workflows.create_base_text_units import run_workflow
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_base_text_units():
    expected = load_test_table("text_units")

    context = await create_test_context()

    config = GraphRagConfig(models=DEFAULT_MODEL_CONFIG)  # type: ignore
    config.chunking.prepend_metadata = ["title"]

    await run_workflow(config, context)

    actual = await load_table_from_storage("text_units", context.output_storage)

    print("EXPECTED")
    print(expected.columns)
    print(expected)

    print("ACTUAL")
    print(actual.columns)
    print(actual)

    compare_outputs(actual, expected, columns=["text", "document_id", "n_tokens"])
