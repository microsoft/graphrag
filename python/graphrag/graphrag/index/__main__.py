# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""The Indexing Engine package root."""

import argparse

from .cli import index_cli

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        help="The configuration yaml file to use when running the pipeline",
        required=False,
        type=str,
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
        help="If no configuration is defined, the root directory to use for input data and output data",
        # Only required if config is not defined
        required=False,
        type=str,
    )
    parser.add_argument(
        "--resume",
        help="Resume a given data run leveraging Parquet output files.",
        # Only required if config is not defined
        required=False,
        type=str,
    )
    parser.add_argument(
        "--reporter",
        help="The progress reporter to use. Valid values are 'rich', 'print', or 'none'",
        type=str,
    )
    parser.add_argument(
        "--emit",
        help="The data formats to emit, comma-separated. Valid values are 'parquet' and 'csv'. default='parquet,csv'",
        type=str,
    )
    parser.add_argument("--nocache", help="Disable LLM cache.", action="store_true")
    args = parser.parse_args()

    index_cli(
        root=args.root,
        verbose=args.verbose,
        resume=args.resume,
        memprofile=args.memprofile,
        nocache=args.nocache,
        reporter=args.reporter,
        config=args.config,
        emit=args.emit,
        cli=True,
    )
