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

class SearchType(Enum):
    """The type of search to run."""

    LOCAL = "local"
    GLOBAL = "global"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value

def cli_main():
    """Parse graphrag cli parameters and execute corresponding cli functions."""
    # Universal command-line arguments
    parser = argparse.ArgumentParser(
        description="The graphrag centralized cli.",
    )
    parser.add_argument(
        "--config",
        help="The configuration yaml file to use.",
        type=file_exist,
    )
    parser.add_argument(
        "--root",
        help="The data project root. Default value: the current directory",
        default=".",
        type=dir_exist,
    )
    subparsers = parser.add_subparsers()

    # Indexing command-line arguments
    parser_index = subparsers.add_parser(
        name="index",
        description="The graphrag indexing engine.",
    )
    parser_index.add_argument(
        "-v",
        "--verbose",
        help="Run the pipeline with verbose logging",
        action="store_true",
    )
    parser_index.add_argument(
        "--memprofile",
        help="Run the pipeline with memory profiling",
        action="store_true",
    )
    parser_index.add_argument(
        "--resume",
        help="Resume a given data run leveraging Parquet output files",
        required=False,
        default="",
        type=str,
    )
    parser_index.add_argument(
        "--reporter",
        help="The progress reporter to use. Default: rich",
        default=ReporterType.RICH,
        type=ReporterType,
        choices=list(ReporterType),
    )
    parser_index.add_argument(
        "--emit",
        help="The data formats to emit, comma-separated. Default: parquet",
        default=TableEmitterType.Parquet.value,
        type=str,
        choices=list(TableEmitterType),
    )
    parser_index.add_argument(
        "--dryrun",
        help="Run the pipeline without executing any steps to inspect/validate the configuration",
        action="store_true",
    )
    parser_index.add_argument(
        "--nocache", help="Disable LLM cache", action="store_true", default=False
    )
    parser_index.add_argument(
        "--init",
        help="Create an initial configuration in the given path",
        action="store_true",
    )
    parser_index.add_argument(
        "--skip-validations",
        help="Skip any preflight validation. Useful when running no LLM steps",
        action="store_true",
    )
    parser_index.add_argument(
        "--update-index",
        help="Update a given index run id, leveraging previous outputs and applying new indexes",
        # Only required if config is not defined
        required=False,
        default=None,
        type=str,
    )
    parser_index.add_argument(
        "--output",
        help="The output directory to use for the pipeline.",
        required=False,
        default=None,
        type=str,
    )
