# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GraphRAG CLI Entry Point."""

import argparse
import asyncio
from enum import Enum

from graphrag.api import DocSelectionType
from graphrag.cli import index_cli, prompt_tune, run_global_search, run_local_search
from graphrag.index.emit.types import TableEmitterType
from graphrag.logging import ReporterType
from graphrag.prompt_tune.generator import MAX_TOKEN_COUNT
from graphrag.prompt_tune.loader import MIN_CHUNK_SIZE
from graphrag.utils.cli import dir_exist, file_exist

INVALID_METHOD_ERROR = "Invalid method"

def cli_main():
    """Parse graphrag cli parameters and execute corresponding cli functions."""

    