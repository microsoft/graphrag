# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The auto templating package root."""

import argparse
import asyncio

from .api import DocSelectionType
from .cli import prompt_tune
from .generator import MAX_TOKEN_COUNT
from .loader import MIN_CHUNK_SIZE

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m graphrag.prompt_tune",
        description="The graphrag auto templating module.",
    )

    parser.add_argument(
        "--config",
        help="Configuration yaml file to use when generating prompts",
        required=True,
        type=str,
    )

    parser.add_argument(
        "--root",
        help="Data project root. Default: current directory",
        required=False,
        type=str,
        default=".",
    )

    parser.add_argument(
        "--domain",
        help="Domain your input data is related to. For example 'space science', 'microbiology', 'environmental news'. If not defined, the domain will be inferred from the input data.",
        required=False,
        default="",
        type=str,
    )

    parser.add_argument(
        "--method",
        help=f"Document selection method. Default: {DocSelectionType.RANDOM}",
        required=False,
        type=DocSelectionType,
        choices=list(DocSelectionType),
        default=DocSelectionType.RANDOM,
    )

    parser.add_argument(
        "--n_subset_max",
        help="Number of text chunks to embed when using auto selection method. Default: 300",
        required=False,
        type=int,
        default=300,
    )

    parser.add_argument(
        "--k",
        help="Maximum number of documents to select from each centroid when using auto selection method. Default: 15",
        required=False,
        type=int,
        default=15,
    )

    parser.add_argument(
        "--limit",
        help="Number of files to load when doing random or top selection. Default: 15",
        type=int,
        required=False,
        default=15,
    )

    parser.add_argument(
        "--max-tokens",
        help=f"Max token count for prompt generation. Default: {MAX_TOKEN_COUNT}",
        type=int,
        required=False,
        default=MAX_TOKEN_COUNT,
    )

    parser.add_argument(
        "--min-examples-required",
        help="Minimum number of examples required in the entity extraction prompt. Default: 2",
        type=int,
        required=False,
        default=2,
    )

    parser.add_argument(
        "--chunk-size",
        help=f"Max token count for prompt generation. Default: {MIN_CHUNK_SIZE}",
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
        help="Directory to save generated prompts to. Default: prompts",
        type=str,
        required=False,
        default="prompts",
    )

    args = parser.parse_args()

    loop = asyncio.get_event_loop()

    loop.run_until_complete(
        prompt_tune(
            args.config,
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
