# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing _get_num_total, chunk, run_strategy and load_strategy methods definitions."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    ProgressTicker,
    VerbCallbacks,
    progress_ticker,
)

from graphrag.index.operations.chunk_text.typing import (
    ChunkInput,
    ChunkStrategy,
    ChunkStrategyType,
)


def chunk_text(
    input: pd.DataFrame,
    column: str,
    to: str,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    Chunk a piece of text into smaller pieces.

    ## Usage
    ```yaml
    args:
        column: <column name> # The name of the column containing the text to chunk, this can either be a column with text, or a column with a list[tuple[doc_id, str]]
        to: <column name> # The name of the column to output the chunks to
        strategy: <strategy config> # The strategy to use to chunk the text, see below for more details
    ```

    ## Strategies
    The text chunk verb uses a strategy to chunk the text. The strategy is an object which defines the strategy to use. The following strategies are available:

    ### tokens
    This strategy uses the [tokens] library to chunk a piece of text. The strategy config is as follows:

    > Note: In the future, this will likely be renamed to something more generic, like "openai_tokens".

    ```yaml
    strategy:
        type: tokens
        chunk_size: 1200 # Optional, The chunk size to use, default: 1200
        chunk_overlap: 100 # Optional, The chunk overlap to use, default: 100
    ```

    ### sentence
    This strategy uses the nltk library to chunk a piece of text into sentences. The strategy config is as follows:

    ```yaml
    strategy:
        type: sentence
    ```
    """
    output = input
    if strategy is None:
        strategy = {}
    strategy_name = strategy.get("type", ChunkStrategyType.tokens)
    strategy_config = {**strategy}
    strategy_exec = load_strategy(strategy_name)

    num_total = _get_num_total(output, column)
    tick = progress_ticker(callbacks.progress, num_total)

    output[to] = output.apply(
        cast(
            Any,
            lambda x: run_strategy(strategy_exec, x[column], strategy_config, tick),
        ),
        axis=1,
    )
    return output


def run_strategy(
    strategy: ChunkStrategy,
    input: ChunkInput,
    strategy_args: dict[str, Any],
    tick: ProgressTicker,
) -> list[str | tuple[list[str] | None, str, int]]:
    """Run strategy method definition."""
    if isinstance(input, str):
        return [item.text_chunk for item in strategy([input], {**strategy_args}, tick)]

    # We can work with both just a list of text content
    # or a list of tuples of (document_id, text content)
    # text_to_chunk = '''
    texts = []
    for item in input:
        if isinstance(item, str):
            texts.append(item)
        else:
            texts.append(item[1])

    strategy_results = strategy(texts, {**strategy_args}, tick)

    results = []
    for strategy_result in strategy_results:
        doc_indices = strategy_result.source_doc_indices
        if isinstance(input[doc_indices[0]], str):
            results.append(strategy_result.text_chunk)
        else:
            doc_ids = [input[doc_idx][0] for doc_idx in doc_indices]
            results.append((
                doc_ids,
                strategy_result.text_chunk,
                strategy_result.n_tokens,
            ))
    return results


def load_strategy(strategy: ChunkStrategyType) -> ChunkStrategy:
    """Load strategy method definition."""
    match strategy:
        case ChunkStrategyType.tokens:
            from graphrag.index.operations.chunk_text.strategies import run_tokens

            return run_tokens
        case ChunkStrategyType.sentence:
            # NLTK
            from graphrag.index.bootstrap import bootstrap
            from graphrag.index.operations.chunk_text.strategies import run_sentences

            bootstrap()
            return run_sentences
        case _:
            msg = f"Unknown strategy: {strategy}"
            raise ValueError(msg)


def _get_num_total(output: pd.DataFrame, column: str) -> int:
    num_total = 0
    for row in output[column]:
        if isinstance(row, str):
            num_total += 1
        else:
            num_total += len(row)
    return num_total
