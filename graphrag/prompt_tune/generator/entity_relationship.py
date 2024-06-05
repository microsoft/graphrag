# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Entity relationship example generation module."""

import asyncio
import json

from graphrag.prompt_tune.prompt import (
    ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT,
    ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
)
from graphrag.llm.types.llm_types import CompletionLLM


async def generate_entity_relationship_examples(
    llm: CompletionLLM,
    persona: str,
    entity_types: str | list[str],
    docs: str | list[str],
    json_mode: bool = False,
) -> list[str]:
    """Generate a list of entity/relationships examples for use in generating an entity configuration.

    Will return entity/relationships examples as either JSON or in tuple_delimiter format depending
    on the json_mode parameter.
    """
    docs_list = [docs] if isinstance(docs, str) else docs

    entity_types_str = (
        entity_types if isinstance(entity_types, str) else ", ".join(entity_types)
    )

    history = [{"role": "system", "content": persona}]

    messages = [
        (
            ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT
            if json_mode
            else ENTITY_RELATIONSHIPS_GENERATION_PROMPT
        ).format(entity_types=entity_types_str, input_text=doc)
        for doc in docs_list
    ]

    tasks = [llm(message, history=history, json=json_mode) for message in messages]

    responses = await asyncio.gather(*tasks)

    return [
        json.dumps(response.json or "") if json_mode else str(response.output)
        for response in responses
    ]
