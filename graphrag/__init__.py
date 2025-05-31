# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GraphRAG package."""

import logging

# Configure the graphrag root logger with a default handler
# This ensures that the logger hierarchy is set up correctly
_root_logger = logging.getLogger("graphrag")
if not _root_logger.handlers:
    # Add a NullHandler to prevent unconfigured logger warnings
    _root_logger.addHandler(logging.NullHandler())
