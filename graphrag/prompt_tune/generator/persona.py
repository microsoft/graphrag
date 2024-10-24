# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Persona generating module for fine-tuning GraphRAG prompts."""

from graphrag.llm.types.llm_types import CompletionLLM
from graphrag.prompt_tune.defaults import DEFAULT_TASK
from graphrag.prompt_tune.prompt.persona import GENERATE_PERSONA_PROMPT


async def generate_persona(
    llm: CompletionLLM, domain: str, task: str = DEFAULT_TASK
) -> str:
    """Generate an LLM persona to use for GraphRAG prompts.

    Parameters
    ----------
    - llm (CompletionLLM): The LLM to use for generation
    - domain (str): The domain to generate a persona for
    - task (str): The task to generate a persona for. Default is DEFAULT_TASK
    """
    formatted_task = task.format(domain=domain)
    persona_prompt = GENERATE_PERSONA_PROMPT.format(sample_task=formatted_task)

    response = await llm(persona_prompt)

    return str(response.output)
