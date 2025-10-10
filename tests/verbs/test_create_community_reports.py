# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.data_model.schemas import COMMUNITY_REPORTS_FINAL_COLUMNS
from graphrag.index.operations.summarize_communities.community_reports_extractor import (
    CommunityReportResponse,
    FindingModel,
)
from graphrag.index.workflows.create_community_reports import (
    run_workflow,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
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


async def test_create_community_reports():
    expected = load_test_table("community_reports")

    context = await create_test_context(
        storage=[
            "covariates",
            "relationships",
            "entities",
            "communities",
        ]
    )

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    config.models["default_chat_model"].type = "mock_chat"
    config.models["default_chat_model"].responses = MOCK_RESPONSES  # type: ignore

    await run_workflow(config, context)

    actual = await load_table_from_storage("community_reports", context.output_storage)

    assert len(actual.columns) == len(expected.columns)

    # only assert a couple of columns that are not mock - most of this table is LLM-generated
    compare_outputs(actual, expected, columns=["community", "level"])

    # assert a handful of mock data items to confirm they get put in the right spot
    assert actual["rank"][:1][0] == 2
    assert actual["rating_explanation"][:1][0] == "<rating_explanation>"

    for column in COMMUNITY_REPORTS_FINAL_COLUMNS:
        assert column in actual.columns
