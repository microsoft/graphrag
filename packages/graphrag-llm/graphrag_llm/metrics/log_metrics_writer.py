# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Log metrics writer implementation."""

import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from graphrag_llm.metrics.metrics_writer import MetricsWriter

if TYPE_CHECKING:
    from graphrag_llm.config import MetricsConfig
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

    _log_method: Callable[..., None] | None = None

    def __init__(self, *, metrics_config: "MetricsConfig", **kwargs: Any) -> None:
        """Initialize LogMetricsWriter."""
        if metrics_config.log_level:
            self._log_method = _log_methods.get(metrics_config.log_level)

    def write_metrics(self, *, id: str, metrics: "Metrics") -> None:
        """Write the given metrics."""
        if self._log_method:
            self._log_method(f"Metrics for {id}: {json.dumps(metrics, indent=2)}")
