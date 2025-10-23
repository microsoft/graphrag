# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GraphRAG package."""
import logging

from .telemetry import setup_telemetry, is_telemetry_disabled

logger = logging.getLogger(__name__)

# Initialize telemetry automatically when the package is imported
# unless explicitly disabled
if not is_telemetry_disabled():
    try:
        setup_telemetry()
        logger.info("Telemetry initialized automatically")
    except Exception as e:
        logger.warning(f"Failed to initialize telemetry: {e}")
else:
    logger.info("Telemetry is not enabled. (Can be enabled via environment variable GRAPHRAG_DISABLE_TELEMETRY)")
