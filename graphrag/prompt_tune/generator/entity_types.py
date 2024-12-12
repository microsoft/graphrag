# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Entity type generation module for fine-tuning."""

from fnllm import ChatLLM
from pydantic import BaseModel

from graphrag.prompt_tune.defaults import DEFAULT_TASK
from graphrag.prompt_tune.prompt.entity_types import (
    ENTITY_TYPE_GENERATION_JSON_PROMPT,
    ENTITY_TYPE_GENERATION_PROMPT,
)


class EntityTypesResponse(BaseModel):
    """Entity types response model."""

    entity_types: list[str]


async def generate_entity_types(
    llm: ChatLLM,
    domain: str,
    persona: str,
    docs: str | list[str],
    task: str = DEFAULT_TASK,
    json_mode: bool = False,
) -> str | list[str]:
    """
    Generate entity type categories from a given set of (small) documents.

    Example Output:
    "entity_types": ['military unit', 'organization', 'person', 'location', 'event', 'date', 'equipment']
    """
    formatted_task = task.format(domain=domain)

    docs_str = "\n".join(docs) if isinstance(docs, list) else docs

    entity_types_prompt = (
        ENTITY_TYPE_GENERATION_JSON_PROMPT
        if json_mode
        else ENTITY_TYPE_GENERATION_PROMPT
    ).format(task=formatted_task, input_text=docs_str)

    history = [{"role": "system", "content": persona}]

    if json_mode:
        response = await llm(
            entity_types_prompt, history=history, json_model=EntityTypesResponse
        )
        model = response.parsed_json
        return model.entity_types if model else []

    response = await llm(entity_types_prompt, history=history, json=json_mode)
    return str(response.output.content)
