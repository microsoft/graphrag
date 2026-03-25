# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

import pandas as pd

from graphrag.data_model.dfs import community_reports_typed
from graphrag.index.operations.finalize_community_reports import finalize_community_reports
from graphrag.query.indexer_adapters import read_indexer_reports


def test_community_report_temporal_fields_flow_to_query_attributes():
    reports = pd.DataFrame(
        [
            {
                "community": 1,
                "level": 0,
                "title": "Community One",
                "summary": "summary",
                "full_content": "full",
                "rank": 5.0,
                "rating_explanation": "important",
                "findings": [{"summary": "f", "explanation": "e"}],
                "current_state": "latest state",
                "timeline_events": [{"summary": "ev1", "explanation": "history"}],
                "superseded_facts": [{"summary": "old", "explanation": "replaced"}],
                "date_range": ["2026-01-01", "2026-01-31"],
                "full_content_json": "{}",
            }
        ]
    )
    communities = pd.DataFrame(
        [
            {
                "community": 1,
                "level": 0,
                "parent": -1,
                "children": [],
                "size": 1,
                "period": "2026",
                "entity_ids": ["entity-1"],
                "title": "entity-title",
            }
        ]
    )

    final_reports = finalize_community_reports(reports, communities)
    typed_reports = community_reports_typed(final_reports.copy())

    assert "current_state" in typed_reports.columns
    assert "timeline_events" in typed_reports.columns
    assert "superseded_facts" in typed_reports.columns
    assert "date_range" in typed_reports.columns

    loaded = read_indexer_reports(
        final_community_reports=typed_reports,
        final_communities=communities,
        community_level=None,
        dynamic_community_selection=True,
    )

    assert loaded[0].attributes is not None
    assert loaded[0].attributes["current_state"] == "latest state"
    assert loaded[0].attributes["timeline_events"][0]["summary"] == "ev1"
    assert loaded[0].attributes["superseded_facts"][0]["summary"] == "old"
    assert loaded[0].attributes["date_range"] == ["2026-01-01", "2026-01-31"]
