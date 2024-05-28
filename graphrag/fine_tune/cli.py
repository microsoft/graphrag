# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for the fine_tune module."""

from pathlib import Path

from datashaper import NoopVerbCallbacks

from graphrag.fine_tune.generator import generate_entity_relationship_examples
from graphrag.fine_tune.loader import read_config_parameters


from graphrag.fine_tune.loader import MIN_CHUNK_SIZE, load_docs_in_chunks
from graphrag.index.llm import load_llm


from graphrag.index.progress import PrintProgressReporter
from graphrag.fine_tune.generator import (
    generate_persona,
    generate_domain,
    create_entity_extraction_prompt,
    generate_entity_types,
    MAX_TOKEN_COUNT,
)

reporter = PrintProgressReporter("")


async def fine_tune(
    root: str,
    domain: str,
    select: str = "top",
    limit: int = 5,
    max_tokens: int = MAX_TOKEN_COUNT,
    chunk_size: int = MIN_CHUNK_SIZE,
    output: str = "prompts",
    **kwargs,
):
    """Fine tune the model."""
    config = read_config_parameters(root, reporter)

    doc_list = await load_docs_in_chunks(
        root=root,
        config=config,
        limit=limit,
        select_method=select,
        reporter=reporter,
        chunk_size=chunk_size,
    )

    # Create LLM from config
    llm = load_llm(
        "fine_tuning",
        config.llm.type,
        NoopVerbCallbacks(),
        None,
        config.llm.model_dump(),
    )

    if not domain:
        domain = await generate_domain(llm, doc_list)
    print(domain)

    persona = await generate_persona(llm, domain)
    print(persona)

    entity_types = await generate_entity_types(
        llm,
        domain=domain,
        persona=persona,
        docs=doc_list,
        json_mode=config.llm.model_supports_json or False,
    )
    print(entity_types)

    examples = await generate_entity_relationship_examples(
        llm,
        persona=persona,
        entity_types=entity_types,
        docs=doc_list,
        json_mode=config.llm.model_supports_json or False,
    )
    print(examples)

    prompt = create_entity_extraction_prompt(
        entity_types=entity_types,
        docs=doc_list,
        examples=examples,
        json_mode=config.llm.model_supports_json or False,
        model_name=config.llm.model,
        output_path=Path(config.root_dir) / output,
        max_token_count=max_tokens,
    )

    print(prompt)
