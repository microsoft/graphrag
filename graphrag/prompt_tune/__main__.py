# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The auto templating package root."""

import argparse
import asyncio

from graphrag.utils.cli import dir_exist, file_exist

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
        type=file_exist,
    )
    parser.add_argument(
        "--root",
        help="Data project root. Default: current directory",
        default=".",
        type=dir_exist,
    )
    parser.add_argument(
        "--domain",
        help="Domain your input data is related to. For example 'space science', 'microbiology', 'environmental news'. If not defined, the domain will be inferred from the input data.",
        type=str,
        default="",
    )
    parser.add_argument(
        "--selection-method",
        help=f"Chunk selection method. Default: {DocSelectionType.RANDOM}",
        type=DocSelectionType,
        choices=list(DocSelectionType),
        default=DocSelectionType.RANDOM,
    )
    parser.add_argument(
        "--n_subset_max",
        help="Number of text chunks to embed when using auto selection method. Default: 300",
        type=int,
        default=300,
    )
    parser.add_argument(
        "--k",
        help="Maximum number of documents to select from each centroid when using auto selection method. Default: 15",
        type=int,
        default=15,
    )
    parser.add_argument(
        "--limit",
        help="Number of documents to load when doing random or top selection. Default: 15",
        type=int,
        default=15,
    )
    parser.add_argument(
        "--max-tokens",
        help=f"Max token count for prompt generation. Default: {MAX_TOKEN_COUNT}",
        type=int,
        default=MAX_TOKEN_COUNT,
    )
    parser.add_argument(
        "--min-examples-required",
        help="Minimum number of examples required in the entity extraction prompt. Default: 2",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--chunk-size",
        help=f"Max token count for prompt generation. Default: {MIN_CHUNK_SIZE}",
        type=int,
        default=MIN_CHUNK_SIZE,
    )
    parser.add_argument(
        "--language",
        help="Primary language used for inputs and outputs on GraphRAG",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--no-entity-types",
        help="Use untyped entity extraction generation",
        action="store_true",
    )
    parser.add_argument(
        "--output",
        help="Directory to save generated prompts to, relative to the root directory. Default: 'prompts'",
        type=str,
        default="prompts",
    )
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        prompt_tune(
            config=args.config,
            root=args.root,
            domain=args.domain,
            selection_method=args.selection_method,
            limit=args.limit,
            max_tokens=args.max_tokens,
            chunk_size=args.chunk_size,
            language=args.language,
            skip_entity_types=args.no_entity_types,
            output=args.output,
            n_subset_max=args.n_subset_max,
            k=args.k,
            min_examples_required=args.min_examples_required,
        )
    )
