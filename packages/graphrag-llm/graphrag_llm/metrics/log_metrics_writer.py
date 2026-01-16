# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Log metrics writer implementation."""

import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from graphrag_llm.metrics.metrics_writer import MetricsWriter

if TYPE_CHECKING:
    from graphrag_llm.types import Metrics

logger = logging.getLogger(__name__)

_log_methods = {
    logging.DEBUG: logger.debug,
    logging.INFO: logger.info,
    logging.WARNING: logger.warning,
    logging.ERROR: logger.error,
    logging.CRITICAL: logger.critical,
}


class LogMetricsWriter(MetricsWriter):
    """Log metrics writer implementation."""

    _log_method: Callable[..., None] = _log_methods[logging.INFO]

    def __init__(self, *, log_level: int | None = None, **kwargs: Any) -> None:
        """Initialize LogMetricsWriter."""
        if log_level and log_level in _log_methods:
            self._log_method = _log_methods[log_level]

    def write_metrics(self, *, id: str, metrics: "Metrics") -> None:
        """Write the given metrics."""
        self._log_method(f"Metrics for {id}: {json.dumps(metrics, indent=2)}")
