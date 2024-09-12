# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine package root."""

import argparse
from enum import Enum
from pathlib import Path

from .cli import index_cli


class ReporterType(Enum):
    """The type of reporter to use."""

    RICH = "rich"
    PRINT = "print"
    NONE = "none"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value


class EmitType(Enum):
    """The type of emitter to use."""

    PARQUET = "parquet"
    CSV = "csv"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value


def file_exist(path):
    """Check for file existence."""
    if not Path(path).is_file():
        msg = f"File not found: {path}"
        raise argparse.ArgumentTypeError(msg)
    return path


def dir_exist(path):
    """Check for directory existence."""
    if not Path(path).is_dir():
        msg = f"Directory not found: {path}"
        raise argparse.ArgumentTypeError(msg)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m graphrag.index",
        description="The graphrag indexing engine",
    )
    parser.add_argument(
        "--config",
        help="The configuration yaml file to use when running the indexing pipeline",
        type=file_exist,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Runs the pipeline with verbose logging",
        action="store_true",
    )
    parser.add_argument(
        "--memprofile",
        help="Runs the pipeline with memory profiling",
        action="store_true",
    )
    parser.add_argument(
        "--root",
        help="If no configuration is defined, the root directory to use for input data and output data. Default: current directory",
        # Only required if config is not defined
        required=False,
        default=".",
        type=dir_exist,
    )
    parser.add_argument(
        "--resume",
        help="Resume a given data run leveraging Parquet output files",
        # Only required if config is not defined
        required=False,
        default="",
        type=str,
    )
    parser.add_argument(
        "--reporter",
        help="The progress reporter to use. Default: rich",
        default=ReporterType.RICH,
        type=ReporterType,
        choices=list(ReporterType),
    )
    parser.add_argument(
        "--emit",
        help="The data formats to emit, comma-separated. Default: parquet",
        default=EmitType.PARQUET,
        type=EmitType,
        choices=list(EmitType),
    )
    parser.add_argument(
        "--dryrun",
        help="Run the pipeline without actually executing any steps and inspect the configuration",
        action="store_true",
    )
    parser.add_argument(
        "--nocache", help="Disable LLM cache", action="store_true", default=False
    )
    parser.add_argument(
        "--init",
        help="Create an initial configuration in the given path",
        action="store_true",
    )
    parser.add_argument(
        "--skip-validations",
        help="Skip any preflight validation. Useful when running no LLM steps",
        action="store_true",
    )
    parser.add_argument(
        "--update-index",
        help="Update a given index run id, leveraging previous outputs and applying new indexes",
        # Only required if config is not defined
        required=False,
        default=None,
        type=str,
    )
    args = parser.parse_args()

    if args.resume and args.update_index:
        msg = "Cannot resume and update a run at the same time"
        raise ValueError(msg)

    index_cli(
        root_dir=args.root,
        verbose=args.verbose,
        resume=args.resume,
        update_index_id=args.update_index,
        memprofile=args.memprofile,
        nocache=args.nocache,
        reporter=args.reporter.value,
        config_filepath=args.config,
        emit=args.emit.value,
        dryrun=args.dryrun,
        init=args.init,
        skip_validations=args.skip_validations,
    )
