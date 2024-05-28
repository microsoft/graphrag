# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


from graphrag.fine_tune.prompt.domain import GENERATE_DOMAIN_PROMPT
from graphrag.llm.types.llm_types import CompletionLLM


async def generate_domain(llm: CompletionLLM, docs: str | list[str]) -> str:
    """Provided a domain and a task, generate an LLM persona to use for GraphRAG prompts"""

    docs_str = " ".join(docs) if isinstance(docs, list) else docs
    domain_prompt = GENERATE_DOMAIN_PROMPT.format(input_text=docs_str)

    response = await llm(domain_prompt)

    return str(response.output)
