# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


import pytest
from datashaper import NoopVerbCallbacks
from datashaper.errors import VerbParallelizationError

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.enums import LLMType
from graphrag.index.operations.summarize_communities.community_reports_extractor.community_reports_extractor import (
    CommunityReportResponse,
    FindingModel,
)
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.create_final_community_reports import (
    run_workflow,
    workflow_name,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    compare_outputs,
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
    inputs = [
        "create_final_nodes",
        "create_final_covariates",
        "create_final_relationships",
        "create_final_entities",
        "create_final_communities",
    ]

    expected = load_test_table(workflow_name)

    config = create_graphrag_config()
    context = create_run_context(None, None, None)

    config.community_reports.strategy = {
        "type": "graph_intelligence",
        "llm": MOCK_LLM_CONFIG,
    }

    for input in inputs:
        table = load_test_table(input)
        await context.storage.set(f"{input}.parquet", table.to_parquet())

    await run_workflow(
        config,
        context,
        NoopVerbCallbacks(),
    )

    actual = await load_table_from_storage(f"{workflow_name}.parquet", context.storage)

    assert len(actual.columns) == len(expected.columns)

    # only assert a couple of columns that are not mock - most of this table is LLM-generated
    compare_outputs(actual, expected, columns=["community", "level"])

    # assert a handful of mock data items to confirm they get put in the right spot
    assert actual["rank"][:1][0] == 2
    assert actual["rank_explanation"][:1][0] == "<rating_explanation>"


async def test_create_final_community_reports_missing_llm_throws():
    inputs = [
        "create_final_nodes",
        "create_final_covariates",
        "create_final_relationships",
        "create_final_entities",
        "create_final_communities",
    ]

    config = create_graphrag_config()
    context = create_run_context(None, None, None)

    config.community_reports.strategy = {
        "type": "graph_intelligence",
    }

    for input in inputs:
        table = load_test_table(input)
        await context.storage.set(f"{input}.parquet", table.to_parquet())

    with pytest.raises(VerbParallelizationError):
        await run_workflow(
            config,
            context,
            NoopVerbCallbacks(),
        )
