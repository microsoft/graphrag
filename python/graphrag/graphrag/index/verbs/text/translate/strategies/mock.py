#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing run and _summarize_text methods definitions."""
from typing import Any

from datashaper import VerbCallbacks

from graphrag.index.cache import PipelineCache

from .typing import TextTranslationResult


async def run(
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
