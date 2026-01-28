# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.data_model.schemas import DOCUMENTS_FINAL_COLUMNS
from graphrag.index.workflows.create_final_documents import (
    run_workflow,
)

from tests.unit.config.utils import get_default_graphrag_config

from .util import (
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_final_documents():
    expected = load_test_table("documents")

    context = await create_test_context(
        storage=["text_units"],
    )

    config = get_default_graphrag_config()

    await run_workflow(config, context)

    actual = await context.output_table_provider.read_dataframe("documents")

    compare_outputs(actual, expected)

    for column in DOCUMENTS_FINAL_COLUMNS:
        assert column in actual.columns
