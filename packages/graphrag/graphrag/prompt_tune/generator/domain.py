# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Domain generation for GraphRAG prompts."""

from typing import TYPE_CHECKING

from graphrag.prompt_tune.prompt.domain import GENERATE_DOMAIN_PROMPT

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion
    from graphrag_llm.types import LLMCompletionResponse


async def generate_domain(model: "LLMCompletion", docs: str | list[str]) -> str:
    """Generate an LLM persona to use for GraphRAG prompts.

    Parameters
    ----------
    - model (LLMCompletion): The LLM to use for generation
    - docs (str | list[str]): The domain to generate a persona for

    Returns
    -------
    - str: The generated domain prompt response.
    """
    docs_str = " ".join(docs) if isinstance(docs, list) else docs
    domain_prompt = GENERATE_DOMAIN_PROMPT.format(input_text=docs_str)

    response: LLMCompletionResponse = await model.completion_async(
        messages=domain_prompt
    )  # type: ignore

    return response.content
