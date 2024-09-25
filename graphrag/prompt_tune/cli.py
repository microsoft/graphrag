# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for the fine_tune module."""

from pathlib import Path

from graphrag.config import load_config
from graphrag.index.progress import PrintProgressReporter

from . import api
from .generator.community_report_summarization import COMMUNITY_SUMMARIZATION_FILENAME
from .generator.entity_extraction_prompt import ENTITY_EXTRACTION_FILENAME
from .generator.entity_summarization_prompt import ENTITY_SUMMARIZATION_FILENAME
from .types import DocSelectionType


async def prompt_tune(
    config: str,
    root: str,
    domain: str,
    selection_method: DocSelectionType,
    limit: int,
    max_tokens: int,
    chunk_size: int,
    language: str | None,
    skip_entity_types: bool,
    output: str,
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
    - selection_method: The chunk selection method.
    - limit: The limit of chunks to load.
    - max_tokens: The maximum number of tokens to use on entity extraction prompts.
    - chunk_size: The chunk token size to use.
    - language: The language to use for the prompts.
    - skip_entity_types: Skip generating entity types.
    - output: The output folder to store the prompts. Relative to the root directory.
    - n_subset_max: The number of text chunks to embed when using auto selection method.
    - k: The number of documents to select when using auto selection method.
    - min_examples_required: The minimum number of examples required for entity extraction prompts.
    """
    reporter = PrintProgressReporter("")
    root_path = Path(root).resolve()
    graph_config = load_config(root_path, config)

    prompts = await api.generate_indexing_prompts(
        config=graph_config,
        root=str(root_path),
        chunk_size=chunk_size,
        limit=limit,
        selection_method=selection_method,
        domain=domain,
        language=language,
        max_tokens=max_tokens,
        skip_entity_types=skip_entity_types,
        min_examples_required=min_examples_required,
        n_subset_max=n_subset_max,
        k=k,
    )

    output_path = (root_path / output).resolve()
    if output_path:
        reporter.info(f"Writing prompts to {output_path}")
        output_path.mkdir(parents=True, exist_ok=True)
        entity_extraction_prompt_path = output_path / ENTITY_EXTRACTION_FILENAME
        entity_summarization_prompt_path = output_path / ENTITY_SUMMARIZATION_FILENAME
        community_summarization_prompt_path = (
            output_path / COMMUNITY_SUMMARIZATION_FILENAME
        )
        # Write files to output path
        with entity_extraction_prompt_path.open("wb") as file:
            file.write(prompts[0].encode(encoding="utf-8", errors="strict"))
        with entity_summarization_prompt_path.open("wb") as file:
            file.write(prompts[1].encode(encoding="utf-8", errors="strict"))
        with community_summarization_prompt_path.open("wb") as file:
            file.write(prompts[2].encode(encoding="utf-8", errors="strict"))
