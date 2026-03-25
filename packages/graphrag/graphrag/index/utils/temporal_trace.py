# Copyright (c) 2026 Microsoft Corporation.
# Licensed under the MIT License

"""Unified temporal trace logging helpers.

Provides a single switch + consistent structured format so operators can trace
how temporal metadata flows across indexing and query stages.
"""

from __future__ import annotations

import json
import os
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_TRACE_ID: ContextVar[str] = ContextVar("graphrag_temporal_trace_id", default="")
_MAX_PREVIEW = 220


def temporal_trace_enabled() -> bool:
    """Return True when temporal trace logging is enabled."""
    value = str(os.getenv("GRAPHRAG_TEMPORAL_TRACE", "0")).strip().lower()
    return value in _TRUE_VALUES


def ensure_trace_id(run_id: str | None = None) -> str:
    """Ensure a trace id exists for the current context and return it."""
    existing = _TRACE_ID.get()
    if existing:
        return existing
    value = run_id or _generate_trace_id()
    _TRACE_ID.set(value)
    return value


def get_trace_id() -> str:
    """Get current trace id if available."""
    return _TRACE_ID.get()


def set_trace_id(run_id: str) -> str:
    """Explicitly set current trace id."""
    _TRACE_ID.set(run_id)
    return run_id


def clear_trace_id() -> None:
    """Clear current trace id from context."""
    _TRACE_ID.set("")


def trace_event(
    logger,
    stage: str,
    event: str,
    *,
    preview_fields: dict[str, Any] | None = None,
    **fields: Any,
) -> None:
    """Emit a readable, stage-scoped temporal trace line.

    Example:
    [TEMPORAL_TRACE][run=20260325-...][stage=chunking][event=chunk_emitted]
    {"doc_id":"...", "turn_range":"3-5", ...}
    """
    if not temporal_trace_enabled():
        return

    run_id = ensure_trace_id()
    payload: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    if preview_fields:
        payload["preview"] = {k: _preview(v) for k, v in preview_fields.items()}

    logger.info(
        "[TEMPORAL_TRACE][run=%s][stage=%s][event=%s] %s",
        run_id,
        stage,
        event,
        json.dumps(payload, ensure_ascii=False, default=str, sort_keys=True),
    )


def _generate_trace_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]


def _preview(value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if len(text) <= _MAX_PREVIEW:
        return text
    return text[:_MAX_PREVIEW] + "...<truncated>"
