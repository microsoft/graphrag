"""Decorators for OpenTelemetry tracing."""

import functools
import inspect
import logging
from typing import Any, Callable, Dict, Optional, TypeVar

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .setup import get_tracer

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

def add_trace(
    operation_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    record_exception: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to trace function or method execution.
    
    Args:
        operation_name: Name for the span. If None, uses function name.
        attributes: Additional attributes to set on the span.
        record_exception: Whether to record exceptions in the span.
    
    Returns:
        Decorated function with tracing.
    """
    def decorator(func: F) -> F:
        tracer = get_tracer(__name__)
        
        # Determine the span name
        span_name = operation_name or f"{func.__module__}.{func.__qualname__}"
        
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(span_name) as span:
                    # Set default attributes
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    # Set custom attributes
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # Set function arguments as attributes (be careful with sensitive data)
                    # _set_function_arguments(span, func, args, kwargs)
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        if record_exception:
                            span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(span_name) as span:
                    # Set default attributes
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    # Set custom attributes
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # Set function arguments as attributes (be careful with sensitive data)
                    # _set_function_arguments(span, func, args, kwargs)
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        if record_exception:
                            span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            
            return sync_wrapper
    
    return decorator

def _set_function_arguments(span: trace.Span, func: Callable, args: tuple, kwargs: dict) -> None:
    """Set function arguments as span attributes, filtering sensitive data."""
    try:
        # Get function signature
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Filter out sensitive arguments
        sensitive_keys = {'password', 'token', 'key', 'secret', 'auth', 'credential'}
        
        for param_name, value in bound_args.arguments.items():
            # Skip sensitive parameters
            if any(sensitive in param_name.lower() for sensitive in sensitive_keys):
                span.set_attribute(f"function.arg.{param_name}", "[REDACTED]")
                continue
            
            # Set attribute based on type
            if isinstance(value, (str, int, float, bool)):
                span.set_attribute(f"function.arg.{param_name}", value)
            elif isinstance(value, (list, tuple)):
                span.set_attribute(f"function.arg.{param_name}.length", len(value))
            elif isinstance(value, dict):
                span.set_attribute(f"function.arg.{param_name}.keys_count", len(value))
            elif value is None:
                span.set_attribute(f"function.arg.{param_name}", "None")
            else:
                span.set_attribute(f"function.arg.{param_name}.type", type(value).__name__)
                
    except Exception as e:
        logger.debug(f"Failed to set function arguments as span attributes: {e}")

def trace_workflow(workflow_name: str) -> Callable[[F], F]:
    """
    Decorator specifically for GraphRAG workflow functions.
    
    Args:
        workflow_name: Name of the workflow for the span.
    
    Returns:
        Decorated function with workflow-specific tracing.
    """
    return add_trace(
        operation_name=f"workflow.{workflow_name}",
        attributes={
            "component": "workflow",
            "workflow.name": workflow_name,
        }
    )

def trace_vector_store_operation(operation_type: str) -> Callable[[F], F]:
    """
    Decorator for vector store operations.
    
    Args:
        operation_type: Type of vector store operation (search, insert, etc.)
    
    Returns:
        Decorated function with vector store-specific tracing.
    """
    return add_trace(
        operation_name=f"vector_store.{operation_type}",
        attributes={
            "component": "vector_store",
            "vector_store.operation": operation_type,
        }
    )

def trace_llm_operation(model_name: Optional[str] = None, operation_name: Optional[str] = "llm.request") -> Callable[[F], F]:
    """
    Decorator for LLM operations.
    
    Args:
        model_name: Name of the LLM model being used.
    
    Returns:
        Decorated function with LLM-specific tracing.
    """
    attributes = {
        "component": "llm",
    }
    if model_name:
        attributes["llm.model"] = model_name
    
    return add_trace(
        operation_name=operation_name,
        attributes=attributes,
    )

def trace_search_operation(operation_type: str) -> Callable[[F], F]:
    """
    Decorator for search operations.
    
    Args:
        operation_type: Type of search operation (query_decomposition, context_building, map_response, reduce_response, etc.)
    
    Returns:
        Decorated function with search-specific tracing.
    """
    return add_trace(
        operation_name=f"search.{operation_type}",
        attributes={
            "component": "search",
            "search.operation": operation_type,
        }
    )

def trace_retrieval_operation(operation_type: str) -> Callable[[F], F]:
    """
    Decorator for retrieval operations.
    
    Args:
        operation_type: Type of retrieval operation (l1_ranking, l2_ranking, relevance_assessment, etc.)
    
    Returns:
        Decorated function with retrieval-specific tracing.
    """
    return add_trace(
        operation_name=f"retrieval.{operation_type}",
        attributes={
            "component": "retrieval",
            "retrieval.operation": operation_type,
        }
    )
