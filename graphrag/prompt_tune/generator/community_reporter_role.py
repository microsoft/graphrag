# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Generate a community reporter role for community summarization."""

from graphrag.language_model.protocol.base import ChatModel
from graphrag.prompt_tune.prompt.community_reporter_role import (
    GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT,
)


async def generate_community_reporter_role(
    model: ChatModel, domain: str, persona: str, docs: str | list[str]
) -> str:
    """Generate an LLM persona to use for GraphRAG prompts.

    Parameters
    ----------
    - llm (CompletionLLM): The LLM to use for generation
    - domain (str): The domain to generate a persona for
    - persona (str): The persona to generate a role for
    - docs (str | list[str]): The domain to generate a persona for

    Returns
    -------
    - str: The generated domain prompt response.
    """
    docs_str = " ".join(docs) if isinstance(docs, list) else docs
    domain_prompt = GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT.format(
        domain=domain, persona=persona, input_text=docs_str
    )

    response = await model.achat(domain_prompt)

    return str(response.output.content)
