"""OpenTelemetry integration for LazyGraphRAG."""

from .setup import setup_telemetry, shutdown_telemetry, get_tracer, get_meter
from .decorators import trace_operation
from .config import TelemetryConfig, is_telemetry_disabled
from .logging_integration import (
    setup_trace_logging,
    TracedLogger,
    add_log_to_span,
    trace_with_logs,
    add_span_annotations,
    set_span_tag,
    mark_span_error,
)

__all__ = [
    "setup_telemetry", 
    "shutdown_telemetry", 
    "get_tracer",
    "get_meter",
    "trace_operation", 
    "TelemetryConfig",
    "is_telemetry_disabled",
    "setup_trace_logging",
    "TracedLogger",
    "add_log_to_span",
    "trace_with_logs",
    "add_span_annotations",
    "set_span_tag",
    "mark_span_error",
]
