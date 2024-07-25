# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Prompt auto templating package root."""

import argparse
import asyncio
from enum import Enum

from graphrag.prompt_tune.generator import MAX_TOKEN_COUNT
from graphrag.prompt_tune.loader import MIN_CHUNK_SIZE

from .cli import prompt_tune


class DocSelectionType(Enum):
    """The type of document selection to use."""

    ALL = "all"
    RANDOM = "random"
    TOP = "top"
    AUTO = "auto"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        help="The data project root. Including the config yml, json or .env",
        required=False,
        type=str,
        default=".",
    )

    parser.add_argument(
        "--domain",
        help="The domain your input data is related to. For example 'space science', 'microbiology', 'environmental news'. If left empty, the domain will be inferred from the input data.",
        required=False,
        default="",
        type=str,
    )

    parser.add_argument(
        "--method",
        help="The method to select documents, one of: all, random, top or auto",
        required=False,
        type=DocSelectionType,
        choices=list(DocSelectionType),
        default=DocSelectionType.RANDOM,
    )

    parser.add_argument(
        "--n_subset_max",
        help="The number of text chunks to embed when using auto selection method",
        required=False,
        type=int,
        default=300,
    )

    parser.add_argument(
        "--k",
        help="The maximum number of documents to select from each centroid when using auto selection method",
        required=False,
        type=int,
        default=15,
    )

    parser.add_argument(
        "--limit",
        help="The limit of files to load when doing random or top selection",
        type=int,
        required=False,
        default=15,
    )

    parser.add_argument(
        "--max-tokens",
        help="Max token count for prompt generation",
        type=int,
        required=False,
        default=MAX_TOKEN_COUNT,
    )

    parser.add_argument(
        "--min-examples-required",
        help="The minimum number of examples required in entity extraction prompt",
        type=int,
        required=False,
        default=2,
    )

    parser.add_argument(
        "--chunk-size",
        help="Max token count for prompt generation",
        type=int,
        required=False,
        default=MIN_CHUNK_SIZE,
    )

    parser.add_argument(
        "--language",
        help="Primary language used for inputs and outputs on GraphRAG",
        type=str,
        required=False,
        default="",
    )

    parser.add_argument(
        "--no-entity-types",
        help="Use untyped entity extraction generation",
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
        prompt_tune(
            args.root,
            args.domain,
            str(args.method),
            args.limit,
            args.max_tokens,
            args.chunk_size,
            args.language,
            args.no_entity_types,
            args.output,
            args.n_subset_max,
            args.k,
            args.min_examples_required,
        )
    )
