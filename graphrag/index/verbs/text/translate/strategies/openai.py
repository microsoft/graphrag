# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run, _translate_text and _create_translation_prompt methods definition."""

import logging
import traceback
from typing import Any

from datashaper import VerbCallbacks

from graphrag.config.enums import LLMType
from graphrag.index.cache import PipelineCache
from graphrag.index.llm import load_llm
from graphrag.index.text_splitting import TokenTextSplitter
from graphrag.llm import CompletionLLM

from .defaults import TRANSLATION_PROMPT as DEFAULT_TRANSLATION_PROMPT
from .typing import TextTranslationResult

log = logging.getLogger(__name__)


async def run(
    input: str | list[str],
    args: dict[str, Any],
    callbacks: VerbCallbacks,
    pipeline_cache: PipelineCache,
) -> TextTranslationResult:
    """Run the Claim extraction chain."""
    llm_config = args.get("llm", {"type": LLMType.StaticResponse})
    llm_type = llm_config.get("type", LLMType.StaticResponse)
    llm = load_llm(
        "text_translation",
        llm_type,
        callbacks,
        pipeline_cache,
        llm_config,
        chat_only=True,
    )
    language = args.get("language", "English")
    prompt = args.get("prompt")
    chunk_size = args.get("chunk_size", 2500)
    chunk_overlap = args.get("chunk_overlap", 0)

    input = [input] if isinstance(input, str) else input
    return TextTranslationResult(
        translations=[
            await _translate_text(
                text, language, prompt, llm, chunk_size, chunk_overlap, callbacks
            )
            for text in input
        ]
    )


async def _translate_text(
    text: str,
    language: str,
    prompt: str | None,
    llm: CompletionLLM,
    chunk_size: int,
    chunk_overlap: int,
    callbacks: VerbCallbacks,
) -> str:
    """Translate a single piece of text."""
    splitter = TokenTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    out = ""
    chunks = splitter.split_text(text)
    for chunk in chunks:
        try:
            result = await llm(
                chunk,
                history=[
                    {
                        "role": "system",
                        "content": (prompt or DEFAULT_TRANSLATION_PROMPT),
                    }
                ],
                variables={"language": language},
            )
            out += result.output or ""
        except Exception as e:
            log.exception("error translating text")
            callbacks.error("Error translating text", e, traceback.format_exc())
            out += ""

    return out
