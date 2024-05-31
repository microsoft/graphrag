# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


from graphrag.fine_tune.prompt.community_reporter_role import (
    GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT,
)
from graphrag.llm.types.llm_types import CompletionLLM


async def generate_community_reporter_role(
    llm: CompletionLLM, domain: str, persona: str, docs: str | list[str]
) -> str:
    """Provided a community reporter role, generate an LLM persona to use for GraphRAG prompts"""

    docs_str = " ".join(docs) if isinstance(docs, list) else docs
    domain_prompt = GENERATE_COMMUNITY_REPORTER_ROLE_PROMPT.format(
        domain=domain, persona=persona, input_text=docs_str
    )

    response = await llm(domain_prompt)

    return str(response.output)
