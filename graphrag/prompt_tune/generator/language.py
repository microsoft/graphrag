# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Language detection for GraphRAG prompts."""

from graphrag.llm.types.llm_types import CompletionLLM
from graphrag.prompt_tune.prompt.language import DETECT_LANGUAGE_PROMPT


async def detect_language(llm: CompletionLLM, docs: str | list[str]) -> str:
    """Detect input language to use for GraphRAG prompts.

    Parameters
    ----------
    - llm (CompletionLLM): The LLM to use for generation
    - docs (str | list[str]): The docs to detect language from

    Returns
    -------
    - str: The detected language.
    """
    docs_str = " ".join(docs) if isinstance(docs, list) else docs
    language_prompt = DETECT_LANGUAGE_PROMPT.format(input_text=docs_str)

    response = await llm(language_prompt)

    return str(response.output)
