# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.operations.summarize_communities.community_reports_extractor import (
    CommunityReportResponse,
    CommunityReportsExtractor,
    FindingModel,
)


def test_community_report_response_supports_temporal_sections():
    report = CommunityReportResponse(
        title="t",
        summary="s",
        findings=[FindingModel(summary="f", explanation="e")],
        current_state="latest",
        timeline_events=[FindingModel(summary="ev", explanation="happened")],
        superseded_facts=[FindingModel(summary="old", explanation="superseded")],
        date_range=["2024-01-01", "2024-01-31"],
        rating=1.0,
        rating_explanation="why",
    )

    assert report.current_state == "latest"
    assert report.timeline_events[0].summary == "ev"
    assert report.superseded_facts[0].summary == "old"
    assert report.date_range == ["2024-01-01", "2024-01-31"]


def test_text_output_includes_current_timeline_and_superseded_sections():
    extractor = CommunityReportsExtractor(
        model=None,  # type: ignore[arg-type]
        extraction_prompt="",
        max_report_length=100,
    )
    report = CommunityReportResponse(
        title="Community A",
        summary="Summary text",
        findings=[FindingModel(summary="Finding", explanation="Finding details")],
        current_state="Current facts",
        timeline_events=[FindingModel(summary="Event 1", explanation="Event details")],
        superseded_facts=[FindingModel(summary="Old fact", explanation="Now obsolete")],
        date_range=["2024-02-01", "2024-02-10"],
        rating=5.0,
        rating_explanation="important",
    )

    output = extractor._get_text_output(report)

    assert "## Current State" in output
    assert "## Timeline" in output
    assert "## Superseded Facts" in output
    assert "## Date Range" in output
    assert "2024-02-01 -> 2024-02-10" in output
