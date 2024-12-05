# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import pytest
from datashaper.errors import VerbParallelizationError
from pandas.testing import assert_series_equal

from graphrag.config.enums import LLMType
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.create_final_covariates import (
    build_steps,
    workflow_name,
)

from .util import (
    get_config_for_workflow,
    get_workflow_output,
    load_input_tables,
    load_test_table,
)

MOCK_LLM_RESPONSES = [
    """
(COMPANY A<|>GOVERNMENT AGENCY B<|>ANTI-COMPETITIVE PRACTICES<|>TRUE<|>2022-01-10T00:00:00<|>2022-01-10T00:00:00<|>Company A was found to engage in anti-competitive practices because it was fined for bid rigging in multiple public tenders published by Government Agency B according to an article published on 2022/01/10<|>According to an article published on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B.)
    """.strip()
]

MOCK_LLM_CONFIG = {"type": LLMType.StaticResponse, "responses": MOCK_LLM_RESPONSES}


async def test_create_final_covariates():
    input_tables = load_input_tables(["workflow:create_base_text_units"])
    expected = load_test_table(workflow_name)

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
    )

    config = get_config_for_workflow(workflow_name)

    config["claim_extract"]["strategy"]["llm"] = MOCK_LLM_CONFIG

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context,
    )

    input = input_tables["workflow:create_base_text_units"]

    assert len(actual.columns) == len(expected.columns)
    # our mock only returns one covariate per text unit, so that's a 1:1 mapping versus the LLM-extracted content in the test data
    assert len(actual) == len(input)

    # assert all of the columns that covariates copied from the input
    assert_series_equal(actual["text_unit_id"], input["id"], check_names=False)

    # make sure the human ids are incrementing
    assert actual["human_readable_id"][0] == 1
    assert actual["human_readable_id"][1] == 2

    # check that the mock data is parsed and inserted into the correct columns
    assert actual["covariate_type"][0] == "claim"
    assert actual["subject_id"][0] == "COMPANY A"
    assert actual["object_id"][0] == "GOVERNMENT AGENCY B"
    assert actual["type"][0] == "ANTI-COMPETITIVE PRACTICES"
    assert actual["status"][0] == "TRUE"
    assert actual["start_date"][0] == "2022-01-10T00:00:00"
    assert actual["end_date"][0] == "2022-01-10T00:00:00"
    assert (
        actual["description"][0]
        == "Company A was found to engage in anti-competitive practices because it was fined for bid rigging in multiple public tenders published by Government Agency B according to an article published on 2022/01/10"
    )
    assert (
        actual["source_text"][0]
        == "According to an article published on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B."
    )


async def test_create_final_covariates_missing_llm_throws():
    input_tables = load_input_tables(["workflow:create_base_text_units"])

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
    )

    config = get_config_for_workflow(workflow_name)

    del config["claim_extract"]["strategy"]["llm"]

    steps = build_steps(config)

    with pytest.raises(VerbParallelizationError):
        await get_workflow_output(
            input_tables,
            {
                "steps": steps,
            },
            context,
        )
