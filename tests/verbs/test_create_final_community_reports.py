# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import json

import pytest
from datashaper.errors import VerbParallelizationError

from graphrag.config.enums import LLMType
from graphrag.index.workflows.v1.create_final_community_reports import (
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

MOCK_RESPONSES = [
    json.dumps({
        "title": "<report_title>",
        "summary": "<executive_summary>",
        "rating": 2,
        "rating_explanation": "<rating_explanation>",
        "findings": [
            {
                "summary": "<insight_1_summary>",
                "explanation": "<insight_1_explanation",
            },
            {
                "summary": "<insight_2_summary>",
                "explanation": "<insight_2_explanation",
            },
        ],
    })
]

MOCK_LLM_CONFIG = {"type": LLMType.StaticResponse, "responses": MOCK_RESPONSES}


async def test_create_final_community_reports():
    input_tables = load_input_tables([
        "workflow:create_final_nodes",
        "workflow:create_final_covariates",
        "workflow:create_final_relationships",
        "workflow:create_final_entities",
        "workflow:create_final_communities",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["create_community_reports"]["strategy"]["llm"] = MOCK_LLM_CONFIG

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    assert len(actual.columns) == len(expected.columns)

    # only assert a couple of columns that are not mock - most of this table is LLM-generated
    compare_outputs(actual, expected, columns=["community", "level"])

    # assert a handful of mock data items to confirm they get put in the right spot
    assert actual["rank"][:1][0] == 2
    assert actual["rank_explanation"][:1][0] == "<rating_explanation>"


async def test_create_final_community_reports_missing_llm_throws():
    input_tables = load_input_tables([
        "workflow:create_final_nodes",
        "workflow:create_final_covariates",
        "workflow:create_final_relationships",
        "workflow:create_final_entities",
        "workflow:create_final_communities",
    ])

    config = get_config_for_workflow(workflow_name)

    # deleting the llm config results in a default mock injection in run_graph_intelligence
    del config["create_community_reports"]["strategy"]["llm"]

    steps = build_steps(config)

    with pytest.raises(VerbParallelizationError):
        await get_workflow_output(
            input_tables,
            {
                "steps": steps,
            },
        )
