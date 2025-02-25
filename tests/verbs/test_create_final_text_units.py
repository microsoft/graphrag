# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_final_text_units import (
    run_workflow,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_final_text_units():
    expected = load_test_table("text_units")

    context = await create_test_context(
        storage=[
            "text_units",
            "entities",
            "relationships",
            "covariates",
        ],
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    config.extract_claims.enabled = True

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage("text_units", context.storage)

    compare_outputs(actual, expected)


async def test_create_final_text_units_no_covariates():
    expected = load_test_table("text_units")

    context = await create_test_context(
        storage=[
            "text_units",
            "entities",
            "relationships",
            "covariates",
        ],
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    config.extract_claims.enabled = False

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage("text_units", context.storage)

    # we're short a covariate_ids column
    columns = list(expected.columns.values)
    columns.remove("covariate_ids")
    compare_outputs(
        actual,
        expected,
        columns=columns,
    )
