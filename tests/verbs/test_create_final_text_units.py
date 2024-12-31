# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from datashaper import NoopVerbCallbacks

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.create_final_text_units import (
    run_workflow,
    workflow_name,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    compare_outputs,
    load_test_table,
)


async def test_create_final_text_units():
    inputs = [
        "create_base_text_units",
        "create_final_entities",
        "create_final_relationships",
        "create_final_covariates",
    ]
    expected = load_test_table(workflow_name)

    context = create_run_context(None, None, None)

    for input in inputs:
        table = load_test_table(input)
        await context.storage.set(f"{input}.parquet", table.to_parquet())

    await context.runtime_storage.set(
        "base_text_units", load_test_table("create_base_text_units")
    )

    config = create_graphrag_config()
    config.claim_extraction.enabled = True

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await load_table_from_storage(f"{workflow_name}.parquet", context.storage)

    compare_outputs(actual, expected)


async def test_create_final_text_units_no_covariates():
    inputs = [
        "create_base_text_units",
        "create_final_entities",
        "create_final_relationships",
        "create_final_covariates",
    ]
    expected = load_test_table(workflow_name)

    context = create_run_context(None, None, None)

    for input in inputs:
        table = load_test_table(input)
        await context.storage.set(f"{input}.parquet", table.to_parquet())

    await context.runtime_storage.set(
        "base_text_units", load_test_table("create_base_text_units")
    )

    config = create_graphrag_config()
    config.claim_extraction.enabled = False

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await load_table_from_storage(f"{workflow_name}.parquet", context.storage)

    # we're short a covariate_ids column
    columns = list(expected.columns.values)
    columns.remove("covariate_ids")
    compare_outputs(
        actual,
        expected,
        columns=columns,
    )
