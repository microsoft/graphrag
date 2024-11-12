# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.create_final_text_units import (
    build_steps,
    workflow_name,
)

from .util import (
    compare_outputs,
    get_config_for_workflow,
    get_workflow_output,
    load_expected,
    load_input_tables,
)


async def test_create_final_text_units():
    input_tables = load_input_tables([
        "workflow:create_base_text_units",
        "workflow:create_final_entities",
        "workflow:create_final_relationships",
        "workflow:create_final_covariates",
    ])
    expected = load_expected(workflow_name)

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
    )

    config = get_config_for_workflow(workflow_name)

    config["covariates_enabled"] = True

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context=context,
    )

    compare_outputs(actual, expected)


async def test_create_final_text_units_no_covariates():
    input_tables = load_input_tables([
        "workflow:create_base_text_units",
        "workflow:create_final_entities",
        "workflow:create_final_relationships",
        "workflow:create_final_covariates",
    ])
    expected = load_expected(workflow_name)

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
    )

    config = get_config_for_workflow(workflow_name)

    config["covariates_enabled"] = False

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context=context,
    )

    # we're short a covariate_ids column
    columns = list(expected.columns.values)
    columns.remove("covariate_ids")
    compare_outputs(
        actual,
        expected,
        columns=columns,
    )
