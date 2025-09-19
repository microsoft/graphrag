# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Auto Templating API.

This API provides access to the auto templating feature of graphrag, allowing external applications
to hook into graphrag and generate prompts from private data.

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

import logging
from typing import Annotated

import annotated_types
from pydantic import PositiveInt, validate_call

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.language_model.manager import ModelManager
from graphrag.logger.standard_logging import init_loggers
from graphrag.prompt_tune.defaults import MAX_TOKEN_COUNT, PROMPT_TUNING_MODEL_ID
from graphrag.prompt_tune.generator.community_report_rating import (
    generate_community_report_rating,
)
from graphrag.prompt_tune.generator.community_report_summarization import (
    create_community_summarization_prompt,
)
from graphrag.prompt_tune.generator.community_reporter_role import (
    generate_community_reporter_role,
)
from graphrag.prompt_tune.generator.domain import generate_domain
from graphrag.prompt_tune.generator.entity_relationship import (
    generate_entity_relationship_examples,
)
from graphrag.prompt_tune.generator.entity_summarization_prompt import (
    create_entity_summarization_prompt,
)
from graphrag.prompt_tune.generator.entity_types import generate_entity_types
from graphrag.prompt_tune.generator.extract_graph_prompt import (
    create_extract_graph_prompt,
)
from graphrag.prompt_tune.generator.language import detect_language
from graphrag.prompt_tune.generator.persona import generate_persona
from graphrag.prompt_tune.loader.input import load_docs_in_chunks
from graphrag.prompt_tune.types import DocSelectionType
from graphrag.tokenizer.get_tokenizer import get_tokenizer

logger = logging.getLogger(__name__)


@validate_call(config={"arbitrary_types_allowed": True})
async def generate_indexing_prompts(
    config: GraphRagConfig,
    chunk_size: PositiveInt = graphrag_config_defaults.chunks.size,
    overlap: Annotated[
        int, annotated_types.Gt(-1)
    ] = graphrag_config_defaults.chunks.overlap,
    limit: PositiveInt = 15,
    selection_method: DocSelectionType = DocSelectionType.RANDOM,
    domain: str | None = None,
    language: str | None = None,
    max_tokens: int = MAX_TOKEN_COUNT,
    discover_entity_types: bool = True,
    min_examples_required: PositiveInt = 2,
    n_subset_max: PositiveInt = 300,
    k: PositiveInt = 15,
    verbose: bool = False,
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
    - discover_entity_types: Generate entity types.
    - min_examples_required: The minimum number of examples required for entity extraction prompts.
    - n_subset_max: The number of text chunks to embed when using auto selection method.
    - k: The number of documents to select when using auto selection method.

    Returns
    -------
    tuple[str, str, str]: entity extraction prompt, entity summarization prompt, community summarization prompt
    """
    init_loggers(config=config, verbose=verbose, filename="prompt-tuning.log")

    # Retrieve documents
    logger.info("Chunking documents...")
    doc_list = await load_docs_in_chunks(
        config=config,
        limit=limit,
        select_method=selection_method,
        logger=logger,
        chunk_size=chunk_size,
        overlap=overlap,
        n_subset_max=n_subset_max,
        k=k,
    )

    # Create LLM from config
    # TODO: Expose a way to specify Prompt Tuning model ID through config
    logger.info("Retrieving language model configuration...")
    default_llm_settings = config.get_language_model_config(PROMPT_TUNING_MODEL_ID)

    logger.info("Creating language model...")
    llm = ModelManager().register_chat(
        name="prompt_tuning",
        model_type=default_llm_settings.type,
        config=default_llm_settings,
        callbacks=NoopWorkflowCallbacks(),
        cache=None,
    )

    if not domain:
        logger.info("Generating domain...")
        domain = await generate_domain(llm, doc_list)

    if not language:
        logger.info("Detecting language...")
        language = await detect_language(llm, doc_list)

    logger.info("Generating persona...")
    persona = await generate_persona(llm, domain)

    logger.info("Generating community report ranking description...")
    community_report_ranking = await generate_community_report_rating(
        llm, domain=domain, persona=persona, docs=doc_list
    )

    entity_types = None
    extract_graph_llm_settings = config.get_language_model_config(
        config.extract_graph.model_id
    )
    if discover_entity_types:
        logger.info("Generating entity types...")
        entity_types = await generate_entity_types(
            llm,
            domain=domain,
            persona=persona,
            docs=doc_list,
            json_mode=extract_graph_llm_settings.model_supports_json or False,
        )

    logger.info("Generating entity relationship examples...")
    examples = await generate_entity_relationship_examples(
        llm,
        persona=persona,
        entity_types=entity_types,
        docs=doc_list,
        language=language,
        json_mode=False,  # config.llm.model_supports_json should be used, but these prompts are used in non-json mode by the index engine
    )

    logger.info("Generating entity extraction prompt...")
    extract_graph_prompt = create_extract_graph_prompt(
        entity_types=entity_types,
        docs=doc_list,
        examples=examples,
        language=language,
        json_mode=False,  # config.llm.model_supports_json should be used, but these prompts are used in non-json mode by the index engine
        tokenizer=get_tokenizer(model_config=extract_graph_llm_settings),
        max_token_count=max_tokens,
        min_examples_required=min_examples_required,
    )

    logger.info("Generating entity summarization prompt...")
    entity_summarization_prompt = create_entity_summarization_prompt(
        persona=persona,
        language=language,
    )

    logger.info("Generating community reporter role...")
    community_reporter_role = await generate_community_reporter_role(
        llm, domain=domain, persona=persona, docs=doc_list
    )

    logger.info("Generating community summarization prompt...")
    community_summarization_prompt = create_community_summarization_prompt(
        persona=persona,
        role=community_reporter_role,
        report_rating_description=community_report_ranking,
        language=language,
    )

    logger.debug("Generated domain: %s", domain)
    logger.debug("Detected language: %s", language)
    logger.debug("Generated persona: %s", persona)

    return (
        extract_graph_prompt,
        entity_summarization_prompt,
        community_summarization_prompt,
    )
