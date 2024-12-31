# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from datashaper import NoopVerbCallbacks

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.index.workflows.create_final_text_units import (
    run_workflow,
    workflow_name,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_final_text_units():
    expected = load_test_table(workflow_name)

    context = await create_test_context(
        storage=[
            "create_final_entities",
            "create_final_relationships",
            "create_final_covariates",
        ],
        runtime_storage=[
            "create_base_text_units",
        ],
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
    expected = load_test_table(workflow_name)

    context = await create_test_context(
        storage=[
            "create_final_entities",
            "create_final_relationships",
            "create_final_covariates",
        ],
        runtime_storage=[
            "create_base_text_units",
        ],
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
