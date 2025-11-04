# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the prompt-tune subcommand."""

import logging
from pathlib import Path

import graphrag.api as api
from graphrag.config.load_config import load_config
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

logger = logging.getLogger(__name__)


async def prompt_tune(
    root: Path,
    config: Path | None,
    domain: str | None,
    verbose: bool,
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
    - verbose: Enable verbose logging.
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

    # configure the root logger with the specified log level
    from graphrag.logger.standard_logging import init_loggers

    # initialize loggers with config
    init_loggers(config=graph_config, verbose=verbose, filename="prompt-tuning.log")

    logger.info("Starting prompt tune.")
    logger.info(
        "Using default configuration: %s",
        redact(graph_config.model_dump()),
    )

    prompts = await api.generate_indexing_prompts(
        config=graph_config,
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
        verbose=verbose,
    )

    output_path = output.resolve()
    if output_path:
        logger.info("Writing prompts to %s", output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        extract_graph_prompt_path = output_path / EXTRACT_GRAPH_FILENAME
        entity_summarization_prompt_path = output_path / ENTITY_SUMMARIZATION_FILENAME
        community_summarization_prompt_path = (
            output_path / COMMUNITY_SUMMARIZATION_FILENAME
        )
        # write files to output path
        with extract_graph_prompt_path.open("wb") as file:
            file.write(prompts[0].encode(encoding="utf-8", errors="strict"))
        with entity_summarization_prompt_path.open("wb") as file:
            file.write(prompts[1].encode(encoding="utf-8", errors="strict"))
        with community_summarization_prompt_path.open("wb") as file:
            file.write(prompts[2].encode(encoding="utf-8", errors="strict"))
        logger.info("Prompts written to %s", output_path)
    else:
        logger.error("No output path provided. Skipping writing prompts.")
