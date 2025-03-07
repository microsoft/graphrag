# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the prompt-tune subcommand."""

from pathlib import Path

import graphrag.api as api
from graphrag.cli.index import _logger
from graphrag.config.load_config import load_config
from graphrag.config.logging import enable_logging_with_config
from graphrag.logger.factory import LoggerFactory, LoggerType
from graphrag.prompt_tune.generator.community_report_summarization import (
    COMMUNITY_SUMMARIZATION_FILENAME,
)
from graphrag.prompt_tune.generator.entity_summarization_prompt import (
    ENTITY_SUMMARIZATION_FILENAME,
)
from graphrag.prompt_tune.generator.extract_graph_prompt import (
    EXTRACT_GRAPH_FILENAME,
)
from graphrag.utils.cli import redact


async def prompt_tune(
    root: Path,
    config: Path | None,
    domain: str | None,
    verbose: bool,
    logger: LoggerType,
    selection_method: api.DocSelectionType,
    limit: int,
    max_tokens: int,
    chunk_size: int,
    overlap: int,
    language: str | None,
    discover_entity_types: bool,
    output: Path,
    n_subset_max: int,
    k: int,
    min_examples_required: int,
):
    """Prompt tune the model.

    Parameters
    ----------
    - config: The configuration file.
    - root: The root directory.
    - domain: The domain to map the input documents to.
    - verbose: Whether to enable verbose logging.
    - logger: The logger to use.
    - selection_method: The chunk selection method.
    - limit: The limit of chunks to load.
    - max_tokens: The maximum number of tokens to use on entity extraction prompts.
    - chunk_size: The chunk token size to use.
    - language: The language to use for the prompts.
    - discover_entity_types: Generate entity types.
    - output: The output folder to store the prompts.
    - n_subset_max: The number of text chunks to embed when using auto selection method.
    - k: The number of documents to select when using auto selection method.
    - min_examples_required: The minimum number of examples required for entity extraction prompts.
    """
    root_path = Path(root).resolve()
    graph_config = load_config(root_path, config)

    # override chunking config in the configuration
    if chunk_size != graph_config.chunks.size:
        graph_config.chunks.size = chunk_size

    if overlap != graph_config.chunks.overlap:
        graph_config.chunks.overlap = overlap

    progress_logger = LoggerFactory().create_logger(logger)
    info, error, success = _logger(progress_logger)

    enabled_logging, log_path = enable_logging_with_config(
        graph_config, verbose, filename="prompt-tune.log"
    )
    if enabled_logging:
        info(f"Logging enabled at {log_path}", verbose)
    else:
        info(
            f"Logging not enabled for config {redact(graph_config.model_dump())}",
            verbose,
        )

    prompts = await api.generate_indexing_prompts(
        config=graph_config,
        root=str(root_path),
        logger=progress_logger,
        chunk_size=chunk_size,
        overlap=overlap,
        limit=limit,
        selection_method=selection_method,
        domain=domain,
        language=language,
        max_tokens=max_tokens,
        discover_entity_types=discover_entity_types,
        min_examples_required=min_examples_required,
        n_subset_max=n_subset_max,
        k=k,
    )

    output_path = output.resolve()
    if output_path:
        info(f"Writing prompts to {output_path}")
        output_path.mkdir(parents=True, exist_ok=True)
        extract_graph_prompt_path = output_path / EXTRACT_GRAPH_FILENAME
        entity_summarization_prompt_path = output_path / ENTITY_SUMMARIZATION_FILENAME
        community_summarization_prompt_path = (
            output_path / COMMUNITY_SUMMARIZATION_FILENAME
        )
        # Write files to output path
        with extract_graph_prompt_path.open("wb") as file:
            file.write(prompts[0].encode(encoding="utf-8", errors="strict"))
        with entity_summarization_prompt_path.open("wb") as file:
            file.write(prompts[1].encode(encoding="utf-8", errors="strict"))
        with community_summarization_prompt_path.open("wb") as file:
            file.write(prompts[2].encode(encoding="utf-8", errors="strict"))
        success(f"Prompts written to {output_path}")
    else:
        error("No output path provided. Skipping writing prompts.")
