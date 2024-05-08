# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing text_translate methods definition."""

from enum import Enum
from typing import Any, cast

import pandas as pd
from datashaper import (
    AsyncType,
    TableContainer,
    VerbCallbacks,
    VerbInput,
    derive_from_rows,
    verb,
)

from graphrag.index.cache import PipelineCache

from .strategies.typing import TextTranslationStrategy


class TextTranslateStrategyType(str, Enum):
    """TextTranslateStrategyType class definition."""

    openai = "openai"
    mock = "mock"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


@verb(name="text_translate")
async def text_translate(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    text_column: str,
    to: str,
    strategy: dict[str, Any],
    async_mode: AsyncType = AsyncType.AsyncIO,
    **kwargs,
) -> TableContainer:
    """
    Translate a piece of text into another language.

    ## Usage
    ```yaml
    verb: text_translate
    args:
        text_column: <column name> # The name of the column containing the text to translate
        to: <column name> # The name of the column to write the translated text to
        strategy: <strategy config> # The strategy to use to translate the text, see below for more details
    ```

    ## Strategies
    The text translate verb uses a strategy to translate the text. The strategy is an object which defines the strategy to use. The following strategies are available:

    ### openai
    This strategy uses openai to translate a piece of text. In particular it uses a LLM to translate a piece of text. The strategy config is as follows:

    ```yaml
    strategy:
        type: openai
        language: english # The language to translate to, default: english
        prompt: <prompt> # The prompt to use for the translation, default: None
        chunk_size: 2500 # The chunk size to use for the translation, default: 2500
        chunk_overlap: 0 # The chunk overlap to use for the translation, default: 0
        llm: # The configuration for the LLM
            type: openai_chat # the type of llm to use, available options are: openai_chat, azure_openai_chat
            api_key: !ENV ${GRAPHRAG_OPENAI_API_KEY} # The api key to use for openai
            model: !ENV ${GRAPHRAG_OPENAI_MODEL:gpt-4-turbo-preview} # The model to use for openai
            max_tokens: !ENV ${GRAPHRAG_MAX_TOKENS:6000} # The max tokens to use for openai
            organization: !ENV ${GRAPHRAG_OPENAI_ORGANIZATION} # The organization to use for openai
    ```
    """
    output_df = cast(pd.DataFrame, input.get_input())
    strategy_type = strategy["type"]
    strategy_args = {**strategy}
    strategy_exec = _load_strategy(strategy_type)

    async def run_strategy(row):
        text = row[text_column]
        result = await strategy_exec(text, strategy_args, callbacks, cache)

        # If it is a single string, then return just the translation for that string
        if isinstance(text, str):
            return result.translations[0]

        # Otherwise, return a list of translations, one for each item in the input
        return list(result.translations)

    results = await derive_from_rows(
        output_df,
        run_strategy,
        callbacks,
        scheduling_type=async_mode,
        num_threads=kwargs.get("num_threads", 4),
    )
    output_df[to] = results
    return TableContainer(table=output_df)


def _load_strategy(strategy: TextTranslateStrategyType) -> TextTranslationStrategy:
    match strategy:
        case TextTranslateStrategyType.openai:
            from .strategies.openai import run as run_openai

            return run_openai

        case TextTranslateStrategyType.mock:
            from .strategies.mock import run as run_mock

            return run_mock

        case _:
            msg = f"Unknown strategy: {strategy}"
            raise ValueError(msg)
