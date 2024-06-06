# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run and _summarize_text methods definitions."""

from typing import Any

from datashaper import VerbCallbacks

from graphrag.index.cache import PipelineCache

from .typing import TextTranslationResult


async def run(  # noqa RUF029 async is required for interface
    input: str | list[str],
    _args: dict[str, Any],
    _reporter: VerbCallbacks,
    _cache: PipelineCache,
) -> TextTranslationResult:
    """Run the Claim extraction chain."""
    input = [input] if isinstance(input, str) else input
    return TextTranslationResult(translations=[_translate_text(text) for text in input])


def _translate_text(text: str) -> str:
    """Translate a single piece of text."""
    return f"{text} translated"
