# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Entity relationship example generation module."""

import asyncio
import json

from graphrag.llm.types.llm_types import CompletionLLM
from graphrag.prompt_tune.prompt.entity_relationship import (
    ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT,
    ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
    UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
)

MAX_EXAMPLES = 5


async def generate_entity_relationship_examples(
    llm: CompletionLLM,
    persona: str,
    entity_types: str | list[str] | None,
    docs: str | list[str],
    language: str,
    json_mode: bool = False,
) -> list[str]:
    """Generate a list of entity/relationships examples for use in generating an entity configuration.

    Will return entity/relationships examples as either JSON or in tuple_delimiter format depending
    on the json_mode parameter.
    """
    docs_list = [docs] if isinstance(docs, str) else docs
    history = [{"role": "system", "content": persona}]

    if entity_types:
        entity_types_str = (
            entity_types
            if isinstance(entity_types, str)
            else ", ".join(map(str, entity_types))
        )

        messages = [
            (
                ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT
                if json_mode
                else ENTITY_RELATIONSHIPS_GENERATION_PROMPT
            ).format(entity_types=entity_types_str, input_text=doc, language=language)
            for doc in docs_list
        ]
    else:
        messages = [
            UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT.format(
                input_text=doc, language=language
            )
            for doc in docs_list
        ]

    messages = messages[:MAX_EXAMPLES]

    tasks = [llm(message, history=history, json=json_mode) for message in messages]

    responses = await asyncio.gather(*tasks)

    return [
        json.dumps(response.json or "") if json_mode else str(response.output)
        for response in responses
    ]
