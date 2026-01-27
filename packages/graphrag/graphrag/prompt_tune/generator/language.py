# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Language detection for GraphRAG prompts."""

from typing import TYPE_CHECKING

from graphrag.prompt_tune.prompt.language import DETECT_LANGUAGE_PROMPT

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion
    from graphrag_llm.types import LLMCompletionResponse


async def detect_language(model: "LLMCompletion", docs: str | list[str]) -> str:
    """Detect input language to use for GraphRAG prompts.

    Parameters
    ----------
    - model (LLMCompletion): The LLM to use for generation
    - docs (str | list[str]): The docs to detect language from

    Returns
    -------
    - str: The detected language.
    """
    docs_str = " ".join(docs) if isinstance(docs, list) else docs
    language_prompt = DETECT_LANGUAGE_PROMPT.format(input_text=docs_str)

    response: LLMCompletionResponse = await model.completion_async(
        messages=language_prompt
    )  # type: ignore

    return response.content
