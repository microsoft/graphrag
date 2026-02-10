# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.workflows.create_base_text_units import run_workflow

from tests.unit.config.utils import get_default_graphrag_config

from .util import (
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_base_text_units():
    expected = load_test_table("text_units")

    context = await create_test_context()

    config = get_default_graphrag_config()
    config.chunking.prepend_metadata = ["title"]

    await run_workflow(config, context)

    actual = await context.output_table_provider.read_dataframe("text_units")

    print("EXPECTED")
    print(expected.columns)
    print(expected)

    print("ACTUAL")
    print(actual.columns)
    print(actual)

    compare_outputs(actual, expected, columns=["text", "document_id", "n_tokens"])
