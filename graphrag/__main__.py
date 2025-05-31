# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GraphRAG package."""

import logging

from graphrag.cli.main import app

# Configure the root logger with a StreamHandler to ensure log messages
# are sent to standard streams when graphrag is run as a command line application
root_logger = logging.getLogger()
if not root_logger.hasHandlers():
    handler = logging.StreamHandler()
    root_logger.addHandler(handler)

app(prog_name="graphrag")
