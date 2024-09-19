# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Auto Templating API.

This API provides access to the auto templating feature of graphrag, allowing external applications
to hook into graphrag and generate prompts from private data.

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

from datashaper import NoopVerbCallbacks
from pydantic import PositiveInt, validate_call

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.llm import load_llm
from graphrag.index.progress import PrintProgressReporter

from .generator import (
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
from .loader import (
    MIN_CHUNK_SIZE,
    load_docs_in_chunks,
)
from .types import DocSelectionType


@validate_call
async def generate_indexing_prompts(
    config: GraphRagConfig,
    root: str,
    chunk_size: PositiveInt = MIN_CHUNK_SIZE,
    limit: PositiveInt = 15,
    selection_method: DocSelectionType = DocSelectionType.RANDOM,
    domain: str | None = None,
    language: str | None = None,
    max_tokens: int = MAX_TOKEN_COUNT,
    skip_entity_types: bool = False,
    min_examples_required: PositiveInt = 2,
    n_subset_max: PositiveInt = 300,
    k: PositiveInt = 15,
) -> tuple[str, str, str]:
    """Generate indexing prompts.

    Parameters
    ----------
    - config: The GraphRag configuration.
    - output_path: The path to store the prompts.
    - chunk_size: The chunk token size to use for input text units.
    - limit: The limit of chunks to load.
    - selection_method: The chunk selection method.
    - domain: The domain to map the input documents to.
    - language: The language to use for the prompts.
    - max_tokens: The maximum number of tokens to use on entity extraction prompts
    - skip_entity_types: Skip generating entity types.
    - min_examples_required: The minimum number of examples required for entity extraction prompts.
    - n_subset_max: The number of text chunks to embed when using auto selection method.
    - k: The number of documents to select when using auto selection method.

    Returns
    -------
    tuple[str, str, str]: entity extraction prompt, entity summarization prompt, community summarization prompt
    """
    reporter = PrintProgressReporter("")

    # Retrieve documents
    doc_list = await load_docs_in_chunks(
        root=root,
        config=config,
        limit=limit,
        select_method=selection_method,
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

    if not domain:
        reporter.info("Generating domain...")
        domain = await generate_domain(llm, doc_list)
        reporter.info(f"Generated domain: {domain}")

    if not language:
        reporter.info("Detecting language...")
        language = await detect_language(llm, doc_list)

    reporter.info("Generating persona...")
    persona = await generate_persona(llm, domain)

    reporter.info("Generating community report ranking description...")
    community_report_ranking = await generate_community_report_rating(
        llm, domain=domain, persona=persona, docs=doc_list
    )

    entity_types = None
    if not skip_entity_types:
        reporter.info("Generating entity types...")
        entity_types = await generate_entity_types(
            llm,
            domain=domain,
            persona=persona,
            docs=doc_list,
            json_mode=config.llm.model_supports_json or False,
        )

    reporter.info("Generating entity relationship examples...")
    examples = await generate_entity_relationship_examples(
        llm,
        persona=persona,
        entity_types=entity_types,
        docs=doc_list,
        language=language,
        json_mode=False,  # config.llm.model_supports_json should be used, but these prompts are used in non-json mode by the index engine
    )

    reporter.info("Generating entity extraction prompt...")
    entity_extraction_prompt = create_entity_extraction_prompt(
        entity_types=entity_types,
        docs=doc_list,
        examples=examples,
        language=language,
        json_mode=False,  # config.llm.model_supports_json should be used, but these prompts are used in non-json mode by the index engine
        encoding_model=config.encoding_model,
        max_token_count=max_tokens,
        min_examples_required=min_examples_required,
    )

    reporter.info("Generating entity summarization prompt...")
    entity_summarization_prompt = create_entity_summarization_prompt(
        persona=persona,
        language=language,
    )

    reporter.info("Generating community reporter role...")
    community_reporter_role = await generate_community_reporter_role(
        llm, domain=domain, persona=persona, docs=doc_list
    )

    reporter.info("Generating community summarization prompt...")
    community_summarization_prompt = create_community_summarization_prompt(
        persona=persona,
        role=community_reporter_role,
        report_rating_description=community_report_ranking,
        language=language,
    )

    return (
        entity_extraction_prompt,
        entity_summarization_prompt,
        community_summarization_prompt,
    )
