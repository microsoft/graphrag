from typing import Any, cast
import pandas as pd
from inspect import iscoroutinefunction

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.chunking_config import ChunkingConfig, ChunkStrategyType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.chunk_text.strategies import run_markdown
from graphrag.index.operations.chunk_text.typing import (
    ChunkInput,
    ChunkStrategy,
)
from graphrag.logger.progress import ProgressTicker, progress_ticker


async def chunk_text(
        input: pd.DataFrame,
        column: str,
        size: int,
        overlap: int,
        encoding_model: str,
        strategy: ChunkStrategyType,
        callbacks: WorkflowCallbacks,
        mainConfig: GraphRagConfig = None
) -> pd.Series:
    """Chunk a piece of text into smaller pieces."""
    strategy_exec = load_strategy(strategy)
    num_total = _get_num_total(input, column)
    tick = progress_ticker(callbacks.progress, num_total)
    config = ChunkingConfig(size=size, overlap=overlap, encoding_model=encoding_model)

    results = []
    for idx, row in input.iterrows():
        result = await run_strategy(strategy_exec, row[column], config, tick, mainConfig)
        results.append(result)

    return pd.Series(results, index=input.index)


async def run_strategy(
    strategy_exec: ChunkStrategy,
    input: ChunkInput,
    config: ChunkingConfig,
    tick: ProgressTicker,
    mainConfig: GraphRagConfig
) -> list[str | tuple[list[str] | None, str, int]]:
    """Run strategy method definition."""
    if isinstance(input, str):
        strategy_results = await strategy_exec([input], config, tick, mainConfig)
        return [item.text_chunk for item in strategy_results]

    # We can work with both just a list of text content
    # or a list of tuples of (document_id, text content)
    texts = []
    for item in input:
        if isinstance(item, str):
            texts.append(item)
        else:
            texts.append(item[1])

    strategy_results = await strategy_exec(texts, config, tick, mainConfig)

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
            from graphrag.index.operations.chunk_text.bootstrap import bootstrap
            from graphrag.index.operations.chunk_text.strategies import run_sentences
            bootstrap()
            return run_sentences
        case ChunkStrategyType.markdown:
            return run_markdown
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