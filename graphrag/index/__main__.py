# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine package root."""

import argparse

from graphrag.utils.cli import dir_exist, file_exist

from .cli import index_cli
from .emit.types import TableEmitterType
from .progress.types import ReporterType

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
        help="Run the pipeline with verbose logging",
        action="store_true",
    )
    parser.add_argument(
        "--memprofile",
        help="Run the pipeline with memory profiling",
        action="store_true",
    )
    parser.add_argument(
        "--root",
        help="The root directory to use for input data and output data, if no configuration is defined. Default: current directory",
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
        default=TableEmitterType.Parquet.value,
        type=str,
        choices=list(TableEmitterType),
    )
    parser.add_argument(
        "--dryrun",
        help="Run the pipeline without executing any steps to inspect/validate the configuration",
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
    parser.add_argument(
        "--output",
        help="The output directory to use for the pipeline.",
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
        reporter=args.reporter,
        config_filepath=args.config,
        emit=[TableEmitterType(value) for value in args.emit.split(",")],
        dryrun=args.dryrun,
        init=args.init,
        skip_validations=args.skip_validations,
        output_dir=args.output,
    )
