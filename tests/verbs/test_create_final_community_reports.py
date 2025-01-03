# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


import pytest

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.enums import LLMType
from graphrag.index.operations.summarize_communities.community_reports_extractor.community_reports_extractor import (
    CommunityReportResponse,
    FindingModel,
)
from graphrag.index.run.derive_from_rows import ParallelizationError
from graphrag.index.workflows.create_final_community_reports import (
    run_workflow,
    workflow_name,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    compare_outputs,
    create_test_context,
    load_test_table,
)

MOCK_RESPONSES = [
    CommunityReportResponse(
        title="<report_title>",
        summary="<executive_summary>",
        rating=2,
        rating_explanation="<rating_explanation>",
        findings=[
            FindingModel(
                summary="<insight_1_summary>", explanation="<insight_1_explanation"
            ),
            FindingModel(
                summary="<insight_2_summary>", explanation="<insight_2_explanation"
            ),
        ],
    )
]

MOCK_LLM_CONFIG = {
    "type": LLMType.StaticResponse,
    "responses": MOCK_RESPONSES,
    "parse_json": True,
}


async def test_create_final_community_reports():
    expected = load_test_table(workflow_name)

    context = await create_test_context(
        storage=[
            "create_final_nodes",
            "create_final_covariates",
            "create_final_relationships",
            "create_final_entities",
            "create_final_communities",
        ]
    )

    config = create_graphrag_config()
    config.community_reports.strategy = {
        "type": "graph_intelligence",
        "llm": MOCK_LLM_CONFIG,
    }

    await run_workflow(
        config,
        context,
        NoopWorkflowCallbacks(),
    )

    actual = await load_table_from_storage(workflow_name, context.storage)

    assert len(actual.columns) == len(expected.columns)

    # only assert a couple of columns that are not mock - most of this table is LLM-generated
    compare_outputs(actual, expected, columns=["community", "level"])

    # assert a handful of mock data items to confirm they get put in the right spot
    assert actual["rank"][:1][0] == 2
    assert actual["rank_explanation"][:1][0] == "<rating_explanation>"


async def test_create_final_community_reports_missing_llm_throws():
    context = await create_test_context(
        storage=[
            "create_final_nodes",
            "create_final_covariates",
            "create_final_relationships",
            "create_final_entities",
            "create_final_communities",
        ]
    )

    config = create_graphrag_config()
    config.community_reports.strategy = {
        "type": "graph_intelligence",
    }

    with pytest.raises(ParallelizationError):
        await run_workflow(
            config,
            context,
            NoopWorkflowCallbacks(),
        )
