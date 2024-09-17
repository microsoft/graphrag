# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.workflows.v1.join_text_units_to_covariate_ids import build_steps

from .util import compare_outputs, get_workflow_output, load_expected, load_input_tables


async def test_join_text_units_to_covariate_ids():
    input_tables = load_input_tables([
        "workflow:create_final_covariates",
    ])
    expected = load_expected("join_text_units_to_covariate_ids")

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": build_steps({}),
        },
    )

    compare_outputs(actual, expected)
