# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for the fine_tune module."""

from pathlib import Path

from datashaper import NoopVerbCallbacks

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.llm import load_llm
from graphrag.index.progress import PrintProgressReporter
from graphrag.index.progress.types import ProgressReporter
from graphrag.llm.types.llm_types import CompletionLLM
from graphrag.prompt_tune.generator import (
    MAX_TOKEN_COUNT,
    create_community_summarization_prompt,
    create_entity_extraction_prompt,
    create_entity_summarization_prompt,
    detect_language,
    generate_community_report_rating,
    generate_community_reporter_role,
    generate_domain,
    generate_entity_relationship_examples,
    generate_entity_types,
    generate_persona,
)
from graphrag.prompt_tune.loader import (
    MIN_CHUNK_SIZE,
    load_docs_in_chunks,
    read_config_parameters,
)


async def prompt_tune(
    root: str,
    domain: str,
    select: str = "random",
    limit: int = 15,
    max_tokens: int = MAX_TOKEN_COUNT,
    chunk_size: int = MIN_CHUNK_SIZE,
    language: str | None = None,
    skip_entity_types: bool = False,
    output: str = "prompts",
    n_subset_max: int = 300,
    k: int = 15,
    min_examples_required: int = 2,
):
    """Prompt tune the model.

    Parameters
    ----------
    - root: The root directory.
    - domain: The domain to map the input documents to.
    - select: The chunk selection method.
    - limit: The limit of chunks to load.
    - max_tokens: The maximum number of tokens to use on entity extraction prompts.
    - chunk_size: The chunk token size to use.
    - skip_entity_types: Skip generating entity types.
    - output: The output folder to store the prompts.
    - n_subset_max: The number of text chunks to embed when using auto selection method.
    - k: The number of documents to select when using auto selection method.
    """
    reporter = PrintProgressReporter("")
    config = read_config_parameters(root, reporter)

    await prompt_tune_with_config(
        root,
        config,
        domain,
        select,
        limit,
        max_tokens,
        chunk_size,
        language,
        skip_entity_types,
        output,
        reporter,
        n_subset_max,
        k,
        min_examples_required,
    )


async def prompt_tune_with_config(
    root: str,
    config: GraphRagConfig,
    domain: str,
    select: str = "random",
    limit: int = 15,
    max_tokens: int = MAX_TOKEN_COUNT,
    chunk_size: int = MIN_CHUNK_SIZE,
    language: str | None = None,
    skip_entity_types: bool = False,
    output: str = "prompts",
    reporter: ProgressReporter | None = None,
    n_subset_max: int = 300,
    k: int = 15,
    min_examples_required: int = 2,
):
    """Prompt tune the model with a configuration.

    Parameters
    ----------
    - root: The root directory.
    - config: The GraphRag configuration.
    - domain: The domain to map the input documents to.
    - select: The chunk selection method.
    - limit: The limit of chunks to load.
    - max_tokens: The maximum number of tokens to use on entity extraction prompts.
    - chunk_size: The chunk token size to use for input text units.
    - skip_entity_types: Skip generating entity types.
    - output: The output folder to store the prompts.
    - reporter: The progress reporter.
    - n_subset_max: The number of text chunks to embed when using auto selection method.
    - k: The number of documents to select when using auto selection method.

    Returns
    -------
    - None
    """
    if not reporter:
        reporter = PrintProgressReporter("")

    output_path = Path(config.root_dir) / output

    doc_list = await load_docs_in_chunks(
        root=root,
        config=config,
        limit=limit,
        select_method=select,
        reporter=reporter,
        chunk_size=chunk_size,
        n_subset_max=n_subset_max,
        k=k,
    )

    # Create LLM from config
    llm = load_llm(
        "prompt_tuning",
        config.llm.type,
        NoopVerbCallbacks(),
        None,
        config.llm.model_dump(),
    )

    await generate_indexing_prompts(
        llm,
        config,
        doc_list,
        output_path,
        reporter,
        domain,
        language,
        max_tokens,
        skip_entity_types,
        min_examples_required,
    )


async def generate_indexing_prompts(
    llm: CompletionLLM,
    config: GraphRagConfig,
    doc_list: list[str],
    output_path: Path,
    reporter: ProgressReporter,
    domain: str | None = None,
    language: str | None = None,
    max_tokens: int = MAX_TOKEN_COUNT,
    skip_entity_types: bool = False,
    min_examples_required: int = 2,
):
    """Generate indexing prompts.

    Parameters
    ----------
    - llm: The LLM model to use.
    - config: The GraphRag configuration.
    - doc_list: The list of documents to use.
    - output_path: The path to store the prompts.
    - reporter: The progress reporter.
    - domain: The domain to map the input documents to.
    - max_tokens: The maximum number of tokens to use on entity extraction prompts
    - skip_entity_types: Skip generating entity types.
    - min_examples_required: The minimum number of examples required for entity extraction prompts.
    """
    if not domain:
        reporter.info("Generating domain...")
        domain = await generate_domain(llm, doc_list)
        reporter.info(f"Generated domain: {domain}")

    if not language:
        reporter.info("Detecting language...")
        language = await detect_language(llm, doc_list)
        reporter.info(f"Detected language: {language}")

    reporter.info("Generating persona...")
    persona = await generate_persona(llm, domain)
    reporter.info(f"Generated persona: {persona}")

    reporter.info("Generating community report ranking description...")
    community_report_ranking = await generate_community_report_rating(
        llm, domain=domain, persona=persona, docs=doc_list
    )
    reporter.info(
        f"Generated community report ranking description: {community_report_ranking}"
    )

    entity_types = None
    if not skip_entity_types:
        reporter.info("Generating entity types")
        entity_types = await generate_entity_types(
            llm,
            domain=domain,
            persona=persona,
            docs=doc_list,
            json_mode=config.llm.model_supports_json or False,
        )
        reporter.info(f"Generated entity types: {entity_types}")

    reporter.info("Generating entity relationship examples...")
    examples = await generate_entity_relationship_examples(
        llm,
        persona=persona,
        entity_types=entity_types,
        docs=doc_list,
        language=language,
        json_mode=False,  # config.llm.model_supports_json should be used, but this prompts are used in non-json by the index engine
    )
    reporter.info("Done generating entity relationship examples")

    reporter.info("Generating entity extraction prompt...")
    create_entity_extraction_prompt(
        entity_types=entity_types,
        docs=doc_list,
        examples=examples,
        language=language,
        json_mode=False,  # config.llm.model_supports_json should be used, but this prompts are used in non-json by the index engine
        output_path=output_path,
        encoding_model=config.encoding_model,
        max_token_count=max_tokens,
        min_examples_required=min_examples_required,
    )
    reporter.info(f"Generated entity extraction prompt, stored in folder {output_path}")

    reporter.info("Generating entity summarization prompt...")
    create_entity_summarization_prompt(
        persona=persona,
        language=language,
        output_path=output_path,
    )
    reporter.info(
        f"Generated entity summarization prompt, stored in folder {output_path}"
    )

    reporter.info("Generating community reporter role...")
    community_reporter_role = await generate_community_reporter_role(
        llm, domain=domain, persona=persona, docs=doc_list
    )
    reporter.info(f"Generated community reporter role: {community_reporter_role}")

    reporter.info("Generating community summarization prompt...")
    create_community_summarization_prompt(
        persona=persona,
        role=community_reporter_role,
        report_rating_description=community_report_ranking,
        language=language,
        output_path=output_path,
    )
    reporter.info(
        f"Generated community summarization prompt, stored in folder {output_path}"
    )
