# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

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
        help="If no configuration is defined, the root directory to use for input data and output data. Default value: the current directory",
        # Only required if config is not defined
        required=False,
        default=".",
        type=str,
    )
    parser.add_argument(
        "--resume",
        help="Resume a given data run leveraging Parquet output files.",
        # Only required if config is not defined
        required=False,
        default=None,
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
    parser.add_argument(
        "--dryrun",
        help="Run the pipeline without actually executing any steps and inspect the configuration.",
        action="store_true",
    )
    parser.add_argument("--nocache", help="Disable LLM cache.", action="store_true")
    parser.add_argument(
        "--init",
        help="Create an initial configuration in the given path.",
        action="store_true",
    )
    parser.add_argument(
        "--skip-validations",
        help="Skip any preflight validation. Useful when running no LLM steps.",
        action="store_true",
    )
    parser.add_argument(
        "--update-index",
        help="Update a given index run id, leveraging previous outputs and applying new indexes.",
        # Only required if config is not defined
        required=False,
        default=None,
        type=str,
    )
    args = parser.parse_args()

    if args.resume and args.update_index:
        msg = "Cannot resume and update a run at the same time."
        raise ValueError(msg)

    index_cli(
        root_dir=args.root,
        verbose=args.verbose or False,
        resume=args.resume,
        update_index_id=args.update_index,
        memprofile=args.memprofile or False,
        nocache=args.nocache or False,
        reporter=args.reporter,
        config_filepath=args.config,
        emit=args.emit,
        dryrun=args.dryrun or False,
        init=args.init or False,
        skip_validations=args.skip_validations or False,
    )
