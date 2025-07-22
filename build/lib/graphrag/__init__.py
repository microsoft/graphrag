# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GraphRAG package."""

import logging

from graphrag.logger.standard_logging import init_console_logger

logger = logging.getLogger(__name__)
init_console_logger()

# Version is set in pyproject.toml
__version__ = "2.4.0"
