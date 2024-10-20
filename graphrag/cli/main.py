# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI entrypoint."""

import argparse
import asyncio
from enum import Enum

from graphrag.api import DocSelectionType
from graphrag.index.emit.types import TableEmitterType
from graphrag.logging import ReporterType
from graphrag.prompt_tune.generator import MAX_TOKEN_COUNT
from graphrag.prompt_tune.loader import MIN_CHUNK_SIZE
from graphrag.utils.cli import dir_exist, file_exist

from .index import index_cli
from .initialize import initialize_project_at
from .prompt_tune import prompt_tune
from .query import run_global_search, run_local_search

INVALID_METHOD_ERROR = "Invalid method"


class SearchType(Enum):
    """The type of search to run."""

    LOCAL = "local"
    GLOBAL = "global"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value


def _call_initialize_cli(args):
    # pass arguments to init
    initialize_project_at(
        path=args.root,
        reporter=args.reporter,
    )


def _call_index_cli(args):
    # pass arguments to index cli
    if args.resume and args.update_index:
        msg = "Cannot resume and update a run at the same time"
        raise ValueError(msg)

    index_cli(
        root_dir=args.root,
        verbose=args.verbose,
        resume=args.resume,
        update_index_id=args.update_index,
        memprofile=args.memprofile,
        no_cache=args.no_cache,
        reporter=args.reporter,
        config_filepath=args.config,
        emit=[TableEmitterType(value.strip()) for value in args.emit.split(",")],
        dry_run=args.dry_run,
        skip_validation=args.skip_validation,
        output_dir=args.output,
    )


def _call_prompt_tune_cli(args):
    # pass arguments to prompt-tune cli
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


def _call_query_cli(args):
    # pass arguments to query cli
    match args.method:
        case SearchType.LOCAL:
            run_local_search(
                config_filepath=args.config,
                data_dir=args.data,
                root_dir=args.root,
                community_level=args.community_level,
                response_type=args.response_type,
                streaming=args.streaming,
                query=args.query[0],
            )
        case SearchType.GLOBAL:
            run_global_search(
                config_filepath=args.config,
                data_dir=args.data,
                root_dir=args.root,
                community_level=args.community_level,
                response_type=args.response_type,
                streaming=args.streaming,
                query=args.query[0],
            )
        case _:
            raise ValueError(INVALID_METHOD_ERROR)


def cli_main():
    """Parse main cli arguments."""
    # set up top-level parser
    parser = argparse.ArgumentParser(
        description="GraphRAG: A graph-based retrieval-augmented generation (RAG) system.",
    )
    subparsers = parser.add_subparsers()

    # init command-line arguments
    parser_init = subparsers.add_parser(
        name="init",
        description="Generate a default configuration file.",
    )
    parser_init.add_argument(
        "--root",
        help="The project root directory. Default value: current directory",
        default=".",
        type=dir_exist,
    )
    parser_init.add_argument(
        "--reporter",
        help="The progress reporter to use. Default: rich",
        default=ReporterType.RICH,
        type=ReporterType,
        choices=list(ReporterType),
    )
    parser_init.set_defaults(func=_call_initialize_cli)

    # index command-line arguments
    parser_index = subparsers.add_parser(
        name="index",
        description="Build a knowledge graph index.",
    )
    parser_index.add_argument(
        "--root",
        help="The project root directory. Default value: current directory",
        default=".",
        type=dir_exist,
    )
    parser_index.add_argument(
        "--config",
        help="The configuration to use.",
        type=file_exist,
    )
    parser_index.add_argument(
        "-v",
        "--verbose",
        help="Run the indexing pipeline with verbose logging",
        action="store_true",
    )
    parser_index.add_argument(
        "--memprofile",
        help="Run the indexing pipeline with memory profiling",
        action="store_true",
    )
    parser_index.add_argument(
        "--resume",
        help="Resume a given indexing run",
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
        "--dry-run",
        help="Run the indexing pipeline without executing any steps to inspect/validate the configuration",
        action="store_true",
    )
    parser_index.add_argument(
        "--no-cache", help="Do not use LLM cache", action="store_true", default=False
    )
    parser_index.add_argument(
        "--skip-validation",
        help="Skip any preflight validation. Useful when running no LLM steps",
        action="store_true",
    )
    parser_index.add_argument(
        "--update-index",
        help="Update an index run id, leveraging previous outputs and applying new indexes",
        required=False,
        default=None,
        type=str,
    )
    parser_index.add_argument(
        "--output",
        help="Indexing pipeline output directory.",
        required=False,
        default=None,
        type=str,
    )
    parser_index.set_defaults(func=_call_index_cli)

    # prompt-tune command-line arguments
    parser_prompt_tune = subparsers.add_parser(
        name="prompt-tune",
        description="Generate custom graphrag prompts with your own data (i.e. auto templating).",
    )
    parser_prompt_tune.add_argument(
        "--root",
        help="The project root directory. Default value: current directory",
        default=".",
        type=dir_exist,
    )
    parser_prompt_tune.add_argument(
        "--config",
        help="The configuration file to use.",
        type=file_exist,
    )
    parser_prompt_tune.add_argument(
        "--domain",
        help="The domain your input data is related to. For example 'space science', 'microbiology', 'environmental news'. If not defined, a domain will be inferred from the input data.",
        type=str,
        default="",
    )
    parser_prompt_tune.add_argument(
        "--selection-method",
        help=f"The text chunk selection method. Default: {DocSelectionType.RANDOM}",
        type=DocSelectionType,
        choices=list(DocSelectionType),
        default=DocSelectionType.RANDOM,
    )
    parser_prompt_tune.add_argument(
        "--n-subset-max",
        help="The number of text chunks to embed when --selection-method=auto. Default: 300",
        type=int,
        default=300,
    )
    parser_prompt_tune.add_argument(
        "--k",
        help="The maximum number of documents to select from each centroid when --selection-method=auto. Default: 15",
        type=int,
        default=15,
    )
    parser_prompt_tune.add_argument(
        "--limit",
        help="The number of documents to load when --selection-method={random,top}. Default: 15",
        type=int,
        default=15,
    )
    parser_prompt_tune.add_argument(
        "--max-tokens",
        help=f"The max token count for prompt generation. Default: {MAX_TOKEN_COUNT}",
        type=int,
        default=MAX_TOKEN_COUNT,
    )
    parser_prompt_tune.add_argument(
        "--min-examples-required",
        help="The minimum number of examples to generate/include in the entity extraction prompt. Default: 2",
        type=int,
        default=2,
    )
    parser_prompt_tune.add_argument(
        "--chunk-size",
        help=f"The max token count for prompt generation. Default: {MIN_CHUNK_SIZE}",
        type=int,
        default=MIN_CHUNK_SIZE,
    )
    parser_prompt_tune.add_argument(
        "--language",
        help="The primary language used for inputs and outputs in graphrag prompts.",
        type=str,
        default=None,
    )
    parser_prompt_tune.add_argument(
        "--no-entity-types",
        help="Enable untyped entity extraction generation.",
        action="store_true",
    )
    parser_prompt_tune.add_argument(
        "--output",
        help="The directory to save prompts to, relative to the project root directory. Default: 'prompts'",
        type=str,
        default="prompts",
    )
    parser_prompt_tune.set_defaults(func=_call_prompt_tune_cli)

    # query command-line arguments
    parser_query = subparsers.add_parser(
        name="query",
        description="Query a knowledge graph index.",
    )
    parser_query.add_argument(
        "--root",
        help="The project root directory. Default value: current directory",
        default=".",
        type=dir_exist,
    )
    parser_query.add_argument(
        "--config",
        help="The configuration file to use.",
        type=file_exist,
    )
    parser_query.add_argument(
        "--data",
        help="Indexing pipeline output directory (i.e. contains the parquet files).",
        type=dir_exist,
    )
    parser_query.add_argument(
        "--method",
        help="The method to run.",
        required=True,
        type=SearchType,
        choices=list(SearchType),
    )
    parser_query.add_argument(
        "--community_level",
        help="The community level in the Leiden community hierarchy from which to load community reports. Higher values represent reports from smaller communities. Default: 2",
        type=int,
        default=2,
    )
    parser_query.add_argument(
        "--response_type",
        help="Free form text describing the response type and format, can be anything, e.g. Multiple Paragraphs, Single Paragraph, Single Sentence, List of 3-7 Points, Single Page, Multi-Page Report. Default: Multiple Paragraphs",
        type=str,
        default="Multiple Paragraphs",
    )
    parser_query.add_argument(
        "--streaming",
        help="Print response in a streaming manner.",
        action="store_true",
    )
    parser_query.add_argument(
        "query",
        nargs=1,
        help="The query to run.",
        type=str,
    )
    parser_query.set_defaults(func=_call_query_cli)

    # parse arguments and call proper cli function
    args = parser.parse_args()
    args.func(args)
