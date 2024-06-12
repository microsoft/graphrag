# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Query Engine package root."""

import argparse
import asyncio
from enum import Enum

from graphrag.prompt_tune.generator import MAX_TOKEN_COUNT
from graphrag.prompt_tune.loader import MIN_CHUNK_SIZE

from .cli import fine_tune


class DocSelectionType(Enum):
    """The type of document selection to use."""

    ALL = "all"
    RANDOM = "random"
    TOP = "top"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        help="The data project root.",
        required=False,
        type=str,
    )

    parser.add_argument(
        "--domain",
        help="The domain your input data is related to. For example 'space science', 'microbiology', 'environmental news'.",
        required=False,
        default="",
        type=str,
    )

    parser.add_argument(
        "--method",
        help="The method to select documents, one of: all, random or top",
        required=True,
        type=DocSelectionType,
        choices=list(DocSelectionType),
        default=DocSelectionType.TOP,
    )

    parser.add_argument(
        "--limit",
        help="The limit of files to load when doing random or top selection",
        type=int,
        required=False,
        default=5,
    )

    parser.add_argument(
        "--max_tokens",
        help="Max token count for prompt generation",
        type=int,
        required=False,
        default=MAX_TOKEN_COUNT,
    )

    parser.add_argument(
        "--chunk_size",
        help="Max token count for prompt generation",
        type=int,
        required=False,
        default=MIN_CHUNK_SIZE,
    )

    parser.add_argument(
        "--untyped",
        help="Use it to run untyped entity extraction generation",
        action="store_true",
        required=False,
        default=False,
    )

    parser.add_argument(
        "--output",
        help="Folder to save the generated prompts to",
        type=str,
        required=False,
        default="prompts",
    )

    args = parser.parse_args()

    loop = asyncio.get_event_loop()

    loop.run_until_complete(
        fine_tune(
            args.root,
            args.domain,
            str(args.method),
            args.limit,
            args.max_tokens,
            args.chunk_size,
            args.untyped,
            args.output,
        )
    )
