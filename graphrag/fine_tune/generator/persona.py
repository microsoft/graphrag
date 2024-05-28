# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.llm.types.llm_types import CompletionLLM
from graphrag.fine_tune.generator.defaults import DEFAULT_TASK
from graphrag.fine_tune.prompt import GENERATE_PERSONA_PROMPT


async def generate_persona(
    llm: CompletionLLM, domain: str, task: str = DEFAULT_TASK
) -> str:
    """Provided a domain and a task, generate an LLM persona to use for GraphRAG prompts"""

    formatted_task = task.format(domain=domain)
    persona_prompt = GENERATE_PERSONA_PROMPT.format(sample_task=formatted_task)

    response = await llm(persona_prompt)

    return str(response.output)
