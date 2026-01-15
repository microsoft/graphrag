"""Generate a rating description for community report rating."""

# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from typing import TYPE_CHECKING

from graphrag.prompt_tune.prompt.community_report_rating import (
    GENERATE_REPORT_RATING_PROMPT,
)

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion
    from graphrag_llm.types import LLMCompletionResponse


async def generate_community_report_rating(
    model: "LLMCompletion", domain: str, persona: str, docs: str | list[str]
) -> str:
    """Generate an LLM persona to use for GraphRAG prompts.

    Parameters
    ----------
    - model (LLMCompletion): The LLM to use for generation
    - domain (str): The domain to generate a rating for
    - persona (str): The persona to generate a rating for for
    - docs (str | list[str]): Documents used to contextualize the rating

    Returns
    -------
    - str: The generated rating description prompt response.
    """
    docs_str = " ".join(docs) if isinstance(docs, list) else docs
    domain_prompt = GENERATE_REPORT_RATING_PROMPT.format(
        domain=domain, persona=persona, input_text=docs_str
    )

    response: LLMCompletionResponse = await model.completion_async(
        messages=domain_prompt
    )  # type: ignore

    return response.content
