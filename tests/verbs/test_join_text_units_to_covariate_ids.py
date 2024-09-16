# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.workflows.v1.join_text_units_to_covariate_ids import build_steps, workflow_name

from .util import compare_outputs, get_config_for_workflow, get_workflow_output, load_expected, load_input_tables


async def test_join_text_units_to_covariate_ids():
    input_tables = load_input_tables([
        "workflow:create_final_covariates",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": build_steps(config),
        },
    )

    compare_outputs(actual, expected)
