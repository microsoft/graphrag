"""Integration between Python logging and OpenTelemetry tracing for Observability visibility."""

import logging
import time
from typing import Any, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


class TracingLogHandler(logging.Handler):
    """
    Custom log handler that adds log messages as span events in OpenTelemetry traces.
    
    This allows you to see log.info(), log.warning(), etc. messages directly in Observability
    as events within the trace spans.
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        """Add log record as an event to the current span."""
        try:
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                # Format the log message
                message = self.format(record)
                
                # Create event attributes
                attributes = {
                    "log.level": record.levelname,
                    "log.logger": record.name,
                    "log.message": message,
                }
                
                # Add exception info if present
                if record.exc_info:
                    attributes["log.exception"] = self.formatException(record.exc_info)
                
                # Add file/line info
                if hasattr(record, 'pathname'):
                    attributes["log.file"] = record.pathname
                    attributes["log.line"] = record.lineno
                    attributes["log.function"] = record.funcName
                
                # Add the log as a span event
                current_span.add_event(
                    name=f"log.{record.levelname.lower()}",
                    attributes=attributes,
                    timestamp=int(record.created * 1_000_000_000)  # Convert to nanoseconds
                )
                
        except Exception:
            # Don't let logging errors break the application
            pass


def setup_trace_logging(logger_name: Optional[str] = None, level: int = logging.INFO) -> None:
    """
    Set up integration between logging and tracing.
    
    After calling this, all log messages from the specified logger (or root logger)
    will appear as events in Observability traces.
    
    Args:
        logger_name: Name of logger to integrate. If None, uses root logger.
        level: Minimum log level to capture in traces.
    """
    logger = logging.getLogger(logger_name)
    
    # Create and configure the tracing handler
    tracing_handler = TracingLogHandler()
    tracing_handler.setLevel(level)
    
    # Use a simple format since detailed info goes in span attributes
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    tracing_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(tracing_handler)


def add_log_to_span(message: str, level: str = "info", **attributes) -> None:
    """
    Manually add a log message to the current span as an event.
    
    Args:
        message: Log message to add
        level: Log level (info, warning, error, etc.)
        **attributes: Additional attributes to include
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        event_attributes = {
            "log.level": level.upper(),
            "log.message": message,
            **attributes
        }
        
        current_span.add_event(
            name=f"log.{level}",
            attributes=event_attributes
        )


def trace_with_logs(span_name: str):
    """
    Context manager that creates a span and captures logs within it.
    
    Usage:
        with trace_with_logs("my_operation") as span:
            logger.info("This will appear in Observability!")
            # Your code here
    """
    tracer = trace.get_tracer(__name__)
    return tracer.start_as_current_span(span_name)


class TracedLogger:
    """
    A logger wrapper that automatically adds logs to the current trace span.
    
    Usage:
        traced_logger = TracedLogger("my_module")
        traced_logger.info("This message will appear in Observability!")
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _log_with_trace(self, level: str, message: str, *args, **kwargs):
        """Log message both to regular logging and as a span event."""
        # Regular logging
        getattr(self.logger, level)(message, *args, **kwargs)
        
        # Add to current span if available
        add_log_to_span(message % args if args else message, level)
    
    def info(self, message: str, *args, **kwargs):
        self._log_with_trace("info", message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        self._log_with_trace("warning", message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        self._log_with_trace("error", message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        self._log_with_trace("debug", message, *args, **kwargs)


def add_span_annotations(*messages: str) -> None:
    """
    Add multiple messages as annotations to the current span.
    These will appear as timeline events in Observability.
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        for message in messages:
            current_span.add_event(message)


def set_span_tag(key: str, value: Any) -> None:
    """Add a tag/attribute to the current span."""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute(key, str(value))


def mark_span_error(error_message: str) -> None:
    """Mark the current span as having an error."""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_status(Status(StatusCode.ERROR, error_message))
        current_span.add_event("error", {"error.message": error_message})
