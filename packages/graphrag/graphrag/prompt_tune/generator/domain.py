# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Domain generation for GraphRAG prompts."""

from graphrag.language_model.protocol.base import ChatModel
from graphrag.prompt_tune.prompt.domain import GENERATE_DOMAIN_PROMPT


async def generate_domain(model: ChatModel, docs: str | list[str]) -> str:
    """Generate an LLM persona to use for GraphRAG prompts.

    Parameters
    ----------
    - llm (CompletionLLM): The LLM to use for generation
    - docs (str | list[str]): The domain to generate a persona for

    Returns
    -------
    - str: The generated domain prompt response.
    """
    docs_str = " ".join(docs) if isinstance(docs, list) else docs
    domain_prompt = GENERATE_DOMAIN_PROMPT.format(input_text=docs_str)

    response = await model.achat(domain_prompt)

    return str(response.output.content)
