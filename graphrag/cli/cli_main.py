# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GraphRAG CLI Entry Point."""

import argparse
import asyncio
from enum import Enum

from graphrag.api import DocSelectionType
from graphrag.index.emit.types import TableEmitterType
from graphrag.logging import ReporterType
from graphrag.prompt_tune.generator import MAX_TOKEN_COUNT
from graphrag.prompt_tune.loader import MIN_CHUNK_SIZE
from graphrag.utils.cli import dir_exist, file_exist

from .index_cli import index_cli
from .prompt_tune_cli import prompt_tune
from .query_cli import run_global_search, run_local_search

INVALID_METHOD_ERROR = "Invalid method"

class SearchType(Enum):
    """The type of search to run."""

    LOCAL = "local"
    GLOBAL = "global"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value

def _call_index_cli(args):
    # Pass arguments to index cli
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

def _call_prompt_tune_cli(args):
    # Pass arguments to prompt-tune cli
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
    # Pass arguments to query cli
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
    """Parse graphrag cli parameters and execute corresponding cli functions."""
    # Universal command-line arguments
    parser = argparse.ArgumentParser(
        description="The graphrag centralized cli.",
    )
    parser.add_argument(
        "--config",
        help="The configuration yaml file to use.",
        type=file_exist,
    )
    parser.add_argument(
        "--root",
        help="The data project root. Default value: the current directory",
        default=".",
        type=dir_exist,
    )
    subparsers = parser.add_subparsers()

    # Indexing command-line arguments
    parser_index = subparsers.add_parser(
        name="index",
        description="The graphrag indexing engine.",
    )
    parser_index.add_argument(
        "-v",
        "--verbose",
        help="Run the pipeline with verbose logging",
        action="store_true",
    )
    parser_index.add_argument(
        "--memprofile",
        help="Run the pipeline with memory profiling",
        action="store_true",
    )
    parser_index.add_argument(
        "--resume",
        help="Resume a given data run leveraging Parquet output files",
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
        "--dryrun",
        help="Run the pipeline without executing any steps to inspect/validate the configuration",
        action="store_true",
    )
    parser_index.add_argument(
        "--nocache", help="Disable LLM cache", action="store_true", default=False
    )
    parser_index.add_argument(
        "--init",
        help="Create an initial configuration in the given path",
        action="store_true",
    )
    parser_index.add_argument(
        "--skip-validations",
        help="Skip any preflight validation. Useful when running no LLM steps",
        action="store_true",
    )
    parser_index.add_argument(
        "--update-index",
        help="Update a given index run id, leveraging previous outputs and applying new indexes",
        required=False,
        default=None,
        type=str,
    )
    parser_index.add_argument(
        "--output",
        help="The output directory to use for the pipeline.",
        required=False,
        default=None,
        type=str,
    )
    parser_index.set_defaults(
        func=_call_index_cli
    )

    # Prompt-tune command-line arguments
    parser_prompt_tune = subparsers.add_parser(
        name="prompt-tune",
        description="The graphrag auto templating module.",
    )
    parser_prompt_tune.add_argument(
        "--domain",
        help="Domain your input data is related to. For example 'space science', 'microbiology', 'environmental news'. If not defined, the domain will be inferred from the input data.",
        type=str,
        default="",
    )
    parser_prompt_tune.add_argument(
        "--selection-method",
        help=f"Chunk selection method. Default: {DocSelectionType.RANDOM}",
        type=DocSelectionType,
        choices=list(DocSelectionType),
        default=DocSelectionType.RANDOM,
    )
    parser_prompt_tune.add_argument(
        "--n_subset_max",
        help="Number of text chunks to embed when using auto selection method. Default: 300",
        type=int,
        default=300,
    )
    parser_prompt_tune.add_argument(
        "--k",
        help="Maximum number of documents to select from each centroid when using auto selection method. Default: 15",
        type=int,
        default=15,
    )
    parser_prompt_tune.add_argument(
        "--limit",
        help="Number of documents to load when doing random or top selection. Default: 15",
        type=int,
        default=15,
    )
    parser_prompt_tune.add_argument(
        "--max-tokens",
        help=f"Max token count for prompt generation. Default: {MAX_TOKEN_COUNT}",
        type=int,
        default=MAX_TOKEN_COUNT,
    )
    parser_prompt_tune.add_argument(
        "--min-examples-required",
        help="Minimum number of examples required in the entity extraction prompt. Default: 2",
        type=int,
        default=2,
    )
    parser_prompt_tune.add_argument(
        "--chunk-size",
        help=f"Max token count for prompt generation. Default: {MIN_CHUNK_SIZE}",
        type=int,
        default=MIN_CHUNK_SIZE,
    )
    parser_prompt_tune.add_argument(
        "--language",
        help="Primary language used for inputs and outputs on GraphRAG",
        type=str,
        default=None,
    )
    parser_prompt_tune.add_argument(
        "--no-entity-types",
        help="Use untyped entity extraction generation",
        action="store_true",
    )
    parser_prompt_tune.add_argument(
        "--output",
        help="Directory to save generated prompts to, relative to the root directory. Default: 'prompts'",
        type=str,
        default="prompts",
    )
    parser_prompt_tune.set_defaults(
        func=_call_prompt_tune_cli
    )

    # Querying command-line arguments
    parser_query = subparsers.add_parser(
        name="query",
        description="The graphrag querying engine.",
    )
    parser_query.add_argument(
        "--data",
        help="The path with the output data from the pipeline",
        type=dir_exist,
    )
    parser_query.add_argument(
        "--method",
        help="The method to run",
        required=True,
        type=SearchType,
        choices=list(SearchType),
    )
    parser_query.add_argument(
        "--community_level",
        help="Community level in the Leiden community hierarchy from which we will load the community reports. A higher value means we will use reports from smaller communities. Default: 2",
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
        help="Print response in a streaming manner",
        action="store_true",
    )
    parser_query.add_argument(
        "query",
        nargs=1,
        help="The query to run",
        type=str,
    )
    parser_query.set_defaults(
        func=_call_query_cli
    )

    # Parse arguments and call cli function
    args = parser.parse_args()
    args.func(args)