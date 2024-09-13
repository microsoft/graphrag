# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Query Engine package root."""

import argparse
from enum import Enum

from graphrag.utils.cli import dir_exist, file_exist

from .cli import run_global_search, run_local_search

INVALID_METHOD_ERROR = "Invalid method"


class SearchType(Enum):
    """The type of search to run."""

    LOCAL = "local"
    GLOBAL = "global"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m graphrag.query",
        description="The graphrag query engine",
    )
    parser.add_argument(
        "--config",
        help="The configuration yaml file to use when running the query",
        required=False,
        type=file_exist,
    )
    parser.add_argument(
        "--data",
        help="The path with the output data from the pipeline",
        type=dir_exist,
    )
    parser.add_argument(
        "--root",
        help="The data project root. Default value: the current directory",
        default=".",
        type=dir_exist,
    )
    parser.add_argument(
        "--method",
        help="The method to run",
        required=True,
        type=SearchType,
        choices=list(SearchType),
    )
    parser.add_argument(
        "--community_level",
        help="Community level in the Leiden community hierarchy from which we will load the community reports. A higher value means we will use reports from smaller communities. Default: 2",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--response_type",
        help="Free form text describing the response type and format, can be anything, e.g. Multiple Paragraphs, Single Paragraph, Single Sentence, List of 3-7 Points, Single Page, Multi-Page Report. Default: Multiple Paragraphs",
        type=str,
        default="Multiple Paragraphs",
    )
    parser.add_argument(
        "--streaming",
        help="Print response in a streaming manner",
        action="store_true",
    )
    parser.add_argument(
        "query",
        nargs=1,
        help="The query to run",
        type=str,
    )
    args = parser.parse_args()

    match args.method:
        case SearchType.LOCAL:
            run_local_search(
                args.config,
                args.data,
                args.root,
                args.community_level,
                args.response_type,
                args.streaming,
                args.query[0],
            )
        case SearchType.GLOBAL:
            run_global_search(
                args.config,
                args.data,
                args.root,
                args.community_level,
                args.response_type,
                args.streaming,
                args.query[0],
            )
        case _:
            raise ValueError(INVALID_METHOD_ERROR)
