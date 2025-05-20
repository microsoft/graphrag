# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI entrypoint."""

import os
import re
from collections.abc import Callable
from pathlib import Path

import typer

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import IndexingMethod, SearchMethod
from graphrag.logger.types import LoggerType
from graphrag.prompt_tune.defaults import LIMIT, MAX_TOKEN_COUNT, N_SUBSET_MAX, K
from graphrag.prompt_tune.types import DocSelectionType

INVALID_METHOD_ERROR = "Invalid method"

app = typer.Typer(
    help="GraphRAG: A graph-based retrieval-augmented generation (RAG) system.",
    no_args_is_help=True,
)


# A workaround for typer's lack of support for proper autocompletion of file/directory paths
# For more detail, watch
#   https://github.com/fastapi/typer/discussions/682
#   https://github.com/fastapi/typer/issues/951
def path_autocomplete(
    file_okay: bool = True,
    dir_okay: bool = True,
    readable: bool = True,
    writable: bool = False,
    match_wildcard: str | None = None,
) -> Callable[[str], list[str]]:
    """Autocomplete file and directory paths."""

    def wildcard_match(string: str, pattern: str) -> bool:
        regex = re.escape(pattern).replace(r"\?", ".").replace(r"\*", ".*")
        return re.fullmatch(regex, string) is not None

    from pathlib import Path

    def completer(incomplete: str) -> list[str]:
        # List items in the current directory as Path objects
        items = Path().iterdir()
        completions = []

        for item in items:
            # Filter based on file/directory properties
            if not file_okay and item.is_file():
                continue
            if not dir_okay and item.is_dir():
                continue
            if readable and not os.access(item, os.R_OK):
                continue
            if writable and not os.access(item, os.W_OK):
                continue

            # Append the name of the matching item
            completions.append(item.name)

        # Apply wildcard matching if required
        if match_wildcard:
            completions = filter(
                lambda i: wildcard_match(i, match_wildcard)
                if match_wildcard
                else False,
                completions,
            )

        # Return completions that start with the given incomplete string
        return [i for i in completions if i.startswith(incomplete)]

    return completer


CONFIG_AUTOCOMPLETE = path_autocomplete(
    file_okay=True,
    dir_okay=False,
    match_wildcard="*.yaml",
    readable=True,
)

ROOT_AUTOCOMPLETE = path_autocomplete(
    file_okay=False,
    dir_okay=True,
    writable=True,
    match_wildcard="*",
)


@app.command("init")
def _initialize_cli(
    root: Path = typer.Option(
        Path(),
        "--root",
        "-r",
        help="The project root directory.",
        dir_okay=True,
        writable=True,
        resolve_path=True,
        autocompletion=ROOT_AUTOCOMPLETE,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force initialization even if the project already exists.",
    ),
) -> None:
    """Generate a default configuration file."""
    from graphrag.cli.initialize import initialize_project_at

    initialize_project_at(path=root, force=force)


@app.command("index")
def _index_cli(
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="The configuration to use.",
        exists=True,
        file_okay=True,
        readable=True,
        autocompletion=CONFIG_AUTOCOMPLETE,
    ),
    root: Path = typer.Option(
        Path(),
        "--root",
        "-r",
        help="The project root directory.",
        exists=True,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        autocompletion=ROOT_AUTOCOMPLETE,
    ),
    method: IndexingMethod = typer.Option(
        IndexingMethod.Standard.value,
        "--method",
        "-m",
        help="The indexing method to use.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Run the indexing pipeline with verbose logging",
    ),
    memprofile: bool = typer.Option(
        False,
        "--memprofile",
        help="Run the indexing pipeline with memory profiling",
    ),
    logger: LoggerType = typer.Option(
        LoggerType.RICH.value,
        "--logger",
        help="The progress logger to use.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help=(
            "Run the indexing pipeline without executing any steps "
            "to inspect and validate the configuration."
        ),
    ),
    cache: bool = typer.Option(
        True,
        "--cache/--no-cache",
        help="Use LLM cache.",
    ),
    skip_validation: bool = typer.Option(
        False,
        "--skip-validation",
        help="Skip any preflight validation. Useful when running no LLM steps.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help=(
            "Indexing pipeline output directory. "
            "Overrides output.base_dir in the configuration file."
        ),
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
) -> None:
    """Build a knowledge graph index."""
    from graphrag.cli.index import index_cli

    index_cli(
        root_dir=root,
        verbose=verbose,
        memprofile=memprofile,
        cache=cache,
        logger=LoggerType(logger),
        config_filepath=config,
        dry_run=dry_run,
        skip_validation=skip_validation,
        output_dir=output,
        method=method,
    )


@app.command("update")
def _update_cli(
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="The configuration to use.",
        exists=True,
        file_okay=True,
        readable=True,
        autocompletion=CONFIG_AUTOCOMPLETE,
    ),
    root: Path = typer.Option(
        Path(),
        "--root",
        "-r",
        help="The project root directory.",
        exists=True,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        autocompletion=ROOT_AUTOCOMPLETE,
    ),
    method: IndexingMethod = typer.Option(
        IndexingMethod.Standard.value,
        "--method",
        "-m",
        help="The indexing method to use.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Run the indexing pipeline with verbose logging.",
    ),
    memprofile: bool = typer.Option(
        False,
        "--memprofile",
        help="Run the indexing pipeline with memory profiling.",
    ),
    logger: LoggerType = typer.Option(
        LoggerType.RICH.value,
        "--logger",
        help="The progress logger to use.",
    ),
    cache: bool = typer.Option(
        True,
        "--cache/--no-cache",
        help="Use LLM cache.",
    ),
    skip_validation: bool = typer.Option(
        False,
        "--skip-validation",
        help="Skip any preflight validation. Useful when running no LLM steps.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help=(
            "Indexing pipeline output directory. "
            "Overrides output.base_dir in the configuration file."
        ),
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
) -> None:
    """
    Update an existing knowledge graph index.

    Applies a default output configuration (if not provided by config), saving the new index to the local file system in the `update_output` folder.
    """
    from graphrag.cli.index import update_cli

    update_cli(
        root_dir=root,
        verbose=verbose,
        memprofile=memprofile,
        cache=cache,
        logger=LoggerType(logger),
        config_filepath=config,
        skip_validation=skip_validation,
        output_dir=output,
        method=method,
    )


@app.command("prompt-tune")
def _prompt_tune_cli(
    root: Path = typer.Option(
        Path(),
        "--root",
        "-r",
        help="The project root directory.",
        exists=True,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        autocompletion=ROOT_AUTOCOMPLETE,
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="The configuration to use.",
        exists=True,
        file_okay=True,
        readable=True,
        autocompletion=CONFIG_AUTOCOMPLETE,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Run the prompt tuning pipeline with verbose logging.",
    ),
    logger: LoggerType = typer.Option(
        LoggerType.RICH.value,
        "--logger",
        help="The progress logger to use.",
    ),
    domain: str | None = typer.Option(
        None,
        "--domain",
        help=(
            "The domain your input data is related to. "
            "For example 'space science', 'microbiology', 'environmental news'. "
            "If not defined, a domain will be inferred from the input data."
        ),
    ),
    selection_method: DocSelectionType = typer.Option(
        DocSelectionType.RANDOM.value,
        "--selection-method",
        help="The text chunk selection method.",
    ),
    n_subset_max: int = typer.Option(
        N_SUBSET_MAX,
        "--n-subset-max",
        help="The number of text chunks to embed when --selection-method=auto.",
    ),
    k: int = typer.Option(
        K,
        "--k",
        help="The maximum number of documents to select from each centroid when --selection-method=auto.",
    ),
    limit: int = typer.Option(
        LIMIT,
        "--limit",
        help="The number of documents to load when --selection-method={random,top}.",
    ),
    max_tokens: int = typer.Option(
        MAX_TOKEN_COUNT,
        "--max-tokens",
        help="The max token count for prompt generation.",
    ),
    min_examples_required: int = typer.Option(
        2,
        "--min-examples-required",
        help="The minimum number of examples to generate/include in the entity extraction prompt.",
    ),
    chunk_size: int = typer.Option(
        graphrag_config_defaults.chunks.size,
        "--chunk-size",
        help="The size of each example text chunk. Overrides chunks.size in the configuration file.",
    ),
    overlap: int = typer.Option(
        graphrag_config_defaults.chunks.overlap,
        "--overlap",
        help="The overlap size for chunking documents. Overrides chunks.overlap in the configuration file.",
    ),
    language: str | None = typer.Option(
        None,
        "--language",
        help="The primary language used for inputs and outputs in graphrag prompts.",
    ),
    discover_entity_types: bool = typer.Option(
        True,
        "--discover-entity-types/--no-discover-entity-types",
        help="Discover and extract unspecified entity types.",
    ),
    output: Path = typer.Option(
        Path("prompts"),
        "--output",
        "-o",
        help="The directory to save prompts to, relative to the project root directory.",
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
) -> None:
    """Generate custom graphrag prompts with your own data (i.e. auto templating)."""
    import asyncio

    from graphrag.cli.prompt_tune import prompt_tune

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        prompt_tune(
            root=root,
            config=config,
            domain=domain,
            verbose=verbose,
            logger=logger,
            selection_method=selection_method,
            limit=limit,
            max_tokens=max_tokens,
            chunk_size=chunk_size,
            overlap=overlap,
            language=language,
            discover_entity_types=discover_entity_types,
            output=output,
            n_subset_max=n_subset_max,
            k=k,
            min_examples_required=min_examples_required,
        )
    )


@app.command("query")
def _query_cli(
    method: SearchMethod = typer.Option(
        ...,
        "--method",
        "-m",
        help="The query algorithm to use.",
    ),
    query: str = typer.Option(
        ...,
        "--query",
        "-q",
        help="The query to execute.",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="The configuration to use.",
        exists=True,
        file_okay=True,
        readable=True,
        autocompletion=CONFIG_AUTOCOMPLETE,
    ),
    data: Path | None = typer.Option(
        None,
        "--data",
        "-d",
        help="Index output directory (contains the parquet files).",
        exists=True,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        autocompletion=ROOT_AUTOCOMPLETE,
    ),
    root: Path = typer.Option(
        Path(),
        "--root",
        "-r",
        help="The project root directory.",
        exists=True,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        autocompletion=ROOT_AUTOCOMPLETE,
    ),
    community_level: int = typer.Option(
        2,
        "--community-level",
        help=(
            "Leiden hierarchy level from which to load community reports. "
            "Higher values represent smaller communities."
        ),
    ),
    dynamic_community_selection: bool = typer.Option(
        False,
        "--dynamic-community-selection/--no-dynamic-selection",
        help="Use global search with dynamic community selection.",
    ),
    response_type: str = typer.Option(
        "Multiple Paragraphs",
        "--response-type",
        help=(
            "Free-form description of the desired response format "
            "(e.g. 'Single Sentence', 'List of 3-7 Points', etc.)."
        ),
    ),
    streaming: bool = typer.Option(
        False,
        "--streaming/--no-streaming",
        help="Print the response in a streaming manner.",
    ),
) -> None:
    """Query a knowledge graph index."""
    from graphrag.cli.query import (
        run_basic_search,
        run_drift_search,
        run_global_search,
        run_local_search,
    )

    match method:
        case SearchMethod.LOCAL:
            run_local_search(
                config_filepath=config,
                data_dir=data,
                root_dir=root,
                community_level=community_level,
                response_type=response_type,
                streaming=streaming,
                query=query,
            )
        case SearchMethod.GLOBAL:
            run_global_search(
                config_filepath=config,
                data_dir=data,
                root_dir=root,
                community_level=community_level,
                dynamic_community_selection=dynamic_community_selection,
                response_type=response_type,
                streaming=streaming,
                query=query,
            )
        case SearchMethod.DRIFT:
            run_drift_search(
                config_filepath=config,
                data_dir=data,
                root_dir=root,
                community_level=community_level,
                streaming=streaming,
                response_type=response_type,
                query=query,
            )
        case SearchMethod.BASIC:
            run_basic_search(
                config_filepath=config,
                data_dir=data,
                root_dir=root,
                streaming=streaming,
                query=query,
            )
        case _:
            raise ValueError(INVALID_METHOD_ERROR)
