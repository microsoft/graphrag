# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import pytest
from pandas.testing import assert_series_equal

from graphrag.callbacks.noop_verb_callbacks import NoopVerbCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.enums import LLMType
from graphrag.index.run.derive_from_rows import ParallelizationError
from graphrag.index.workflows.create_final_covariates import (
    run_workflow,
    workflow_name,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    create_test_context,
    load_test_table,
)

MOCK_LLM_RESPONSES = [
    """
(COMPANY A<|>GOVERNMENT AGENCY B<|>ANTI-COMPETITIVE PRACTICES<|>TRUE<|>2022-01-10T00:00:00<|>2022-01-10T00:00:00<|>Company A was found to engage in anti-competitive practices because it was fined for bid rigging in multiple public tenders published by Government Agency B according to an article published on 2022/01/10<|>According to an article published on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B.)
    """.strip()
]

MOCK_LLM_CONFIG = {"type": LLMType.StaticResponse, "responses": MOCK_LLM_RESPONSES}


async def test_create_final_covariates():
    input = load_test_table("create_base_text_units")
    expected = load_test_table(workflow_name)

    context = await create_test_context(
        storage=["create_base_text_units"],
    )

    config = create_graphrag_config()
    config.claim_extraction.strategy = {
        "type": "graph_intelligence",
        "llm": MOCK_LLM_CONFIG,
        "claim_description": "description",
    }

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await load_table_from_storage(workflow_name, context.storage)

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
    context = await create_test_context(
        storage=["create_base_text_units"],
    )

    config = create_graphrag_config()
    config.claim_extraction.strategy = {
        "type": "graph_intelligence",
        "claim_description": "description",
    }

    with pytest.raises(ParallelizationError):
        await run_workflow(
            config,
            context,
            NoopVerbCallbacks(),
        )
