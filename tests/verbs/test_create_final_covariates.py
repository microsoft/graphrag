# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import json

from graphrag.index.workflows.v1.create_final_covariates import (
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

from graphrag.index.verbs.covariates.extract_covariates.strategies.graph_intelligence.defaults import MOCK_LLM_RESPONSES


async def test_create_final_covariates():
    input_tables = load_input_tables(["workflow:create_base_text_units"])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    # deleting the llm config results in a default mock injection in run_gi_extract_claims
    del config["claim_extract"]["strategy"]["llm"]
    
    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    input = input_tables["workflow:create_base_text_units"]
    assert len(actual.columns) == len(expected.columns)
    # our mock only returns one covariate per text unit, so that's a 1:1 mapping versus the LLM-extracted content in the test data
    assert len(actual) == len(input)
