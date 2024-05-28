# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for the fine_tune module."""

import os
from pathlib import Path
from typing import cast

from datashaper import NoopVerbCallbacks, TableContainer, VerbInput

from graphrag.fine_tune.generator import generate_entity_relationship_examples
from graphrag.fine_tune.loader.config import _read_config_parameters


from graphrag.fine_tune.loader.input import load_docs_in_chunks
from graphrag.index.llm import load_llm

import pandas as pd


from graphrag.index.progress import PrintProgressReporter
from graphrag.fine_tune.generator import generate_entity_types
from graphrag.fine_tune.generator import (
    generate_persona,
    generate_domain,
    create_entity_extraction_prompt,
)

reporter = PrintProgressReporter("")


async def fine_tune(
    root: str,
    domain: str,
    select: str = "top",
    limit: int = 5,
    output: str = "prompts",
    **kwargs,
):
    """Fine tune the model."""
    config = _read_config_parameters(root, reporter)

    doc_list = await load_docs_in_chunks(
        root=root, config=config, limit=limit, select_method=select, reporter=reporter
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
        output_path=Path(config.root_dir) / output / "entity_extraction_prompt.txt",
    )

    print(prompt)
