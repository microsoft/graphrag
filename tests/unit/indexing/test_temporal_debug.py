# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

import logging

from graphrag.index.utils.temporal_trace import (
    clear_trace_id,
    ensure_trace_id,
    temporal_trace_enabled,
    trace_event,
)


def test_temporal_trace_disabled_by_default(monkeypatch):
    monkeypatch.delenv("GRAPHRAG_TEMPORAL_TRACE", raising=False)
    assert temporal_trace_enabled() is False


def test_temporal_trace_enabled_for_truthy_values(monkeypatch):
    monkeypatch.setenv("GRAPHRAG_TEMPORAL_TRACE", "true")
    assert temporal_trace_enabled() is True


def test_temporal_trace_logs_use_stage_event_format(monkeypatch, caplog):
    monkeypatch.setenv("GRAPHRAG_TEMPORAL_TRACE", "1")
    clear_trace_id()
    ensure_trace_id("trace-test")
    logger = logging.getLogger("graphrag.test.temporal_trace")
    with caplog.at_level(logging.INFO):
        trace_event(
            logger,
            stage="chunking",
            event="text_unit_emitted",
            conversation_id="conv-1",
            start_turn_index=1,
            end_turn_index=2,
        )

    assert "[TEMPORAL_TRACE][run=trace-test][stage=chunking][event=text_unit_emitted]" in caplog.text
