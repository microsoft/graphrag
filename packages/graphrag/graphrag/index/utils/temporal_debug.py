# Copyright (c) 2026 Microsoft Corporation.
# Licensed under the MIT License

"""Compatibility wrapper for temporal trace toggle.

Deprecated: prefer ``temporal_trace_enabled`` in ``temporal_trace.py``.
"""

from __future__ import annotations

from graphrag.index.utils.temporal_trace import temporal_trace_enabled


def temporal_debug_enabled() -> bool:
    """Backward-compatible alias for temporal trace toggle.

    ``GRAPHRAG_TEMPORAL_TRACE`` is the canonical switch.
    """
    return temporal_trace_enabled()
