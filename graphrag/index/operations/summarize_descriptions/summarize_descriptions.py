# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the summarize_descriptions verb."""

import asyncio
import logging
from typing import Any

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.operations.summarize_descriptions.typing import (
    SummarizationStrategy,
    SummarizeStrategyType,
)
from graphrag.logger.progress import ProgressTicker, progress_ticker

log = logging.getLogger(__name__)


async def summarize_descriptions(
    entities_df: pd.DataFrame,
    relationships_df: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    strategy: dict[str, Any] | None = None,
    num_threads: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Summarize entity and relationship descriptions from an entity graph.

    ## Usage

    To turn this feature ON please set the environment variable `GRAPHRAG_SUMMARIZE_DESCRIPTIONS_ENABLED=True`.

    ### yaml

    ```yaml
    args:
        strategy: <strategy_config>, see strategies section below
    ```

    ## Strategies

    The summarize descriptions verb uses a strategy to summarize descriptions for entities. The strategy is a json object which defines the strategy to use. The following strategies are available:

    ### graph_intelligence

    This strategy uses the [graph_intelligence] library to summarize descriptions for entities. The strategy config is as follows:

    ```yml
    strategy:
        type: graph_intelligence
        summarize_prompt: # Optional, the prompt to use for extraction


        llm: # The configuration for the LLM
            type: openai # the type of llm to use, available options are: openai, azure, openai_chat, azure_openai_chat.  The last two being chat based LLMs.
            api_key: !ENV ${GRAPHRAG_OPENAI_API_KEY} # The api key to use for openai
            model: !ENV ${GRAPHRAG_OPENAI_MODEL:gpt-4-turbo-preview} # The model to use for openai
            max_tokens: !ENV ${GRAPHRAG_MAX_TOKENS:6000} # The max tokens to use for openai
            organization: !ENV ${GRAPHRAG_OPENAI_ORGANIZATION} # The organization to use for openai

            # if using azure flavor
            api_base: !ENV ${GRAPHRAG_OPENAI_API_BASE} # The api base to use for azure
            api_version: !ENV ${GRAPHRAG_OPENAI_API_VERSION} # The api version to use for azure
            proxy: !ENV ${GRAPHRAG_OPENAI_PROXY} # The proxy to use for azure
    ```
    """
    log.debug("summarize_descriptions strategy=%s", strategy)
    strategy = strategy or {}
    strategy_exec = load_strategy(
        strategy.get("type", SummarizeStrategyType.graph_intelligence)
    )
    strategy_config = {**strategy}

    # if max_retries is not set, inject a dynamically assigned value based on the maximum number of expected LLM calls to be made
    if strategy_config.get("llm") and strategy_config["llm"]["max_retries"] == -1:
        strategy_config["llm"]["max_retries"] = len(entities_df) + len(relationships_df)

    async def get_summarized(
        nodes: pd.DataFrame, edges: pd.DataFrame, semaphore: asyncio.Semaphore
    ):
        ticker_length = len(nodes) + len(edges)

        ticker = progress_ticker(callbacks.progress, ticker_length)

        node_futures = [
            do_summarize_descriptions(
                str(row.title),  # type: ignore
                sorted(set(row.description)),  # type: ignore
                ticker,
                semaphore,
            )
            for row in nodes.itertuples(index=False)
        ]

        node_results = await asyncio.gather(*node_futures)

        node_descriptions = [
            {
                "title": result.id,
                "description": result.description,
            }
            for result in node_results
        ]

        edge_futures = [
            do_summarize_descriptions(
                (str(row.source), str(row.target)),  # type: ignore
                sorted(set(row.description)),  # type: ignore
                ticker,
                semaphore,
            )
            for row in edges.itertuples(index=False)
        ]

        edge_results = await asyncio.gather(*edge_futures)

        edge_descriptions = [
            {
                "source": result.id[0],
                "target": result.id[1],
                "description": result.description,
            }
            for result in edge_results
        ]

        entity_descriptions = pd.DataFrame(node_descriptions)
        relationship_descriptions = pd.DataFrame(edge_descriptions)
        return entity_descriptions, relationship_descriptions

    async def do_summarize_descriptions(
        id: str | tuple[str, str],
        descriptions: list[str],
        ticker: ProgressTicker,
        semaphore: asyncio.Semaphore,
    ):
        async with semaphore:
            results = await strategy_exec(
                id, descriptions, callbacks, cache, strategy_config
            )
            ticker(1)
        return results

    semaphore = asyncio.Semaphore(num_threads)

    return await get_summarized(entities_df, relationships_df, semaphore)


def load_strategy(strategy_type: SummarizeStrategyType) -> SummarizationStrategy:
    """Load strategy method definition."""
    match strategy_type:
        case SummarizeStrategyType.graph_intelligence:
            from graphrag.index.operations.summarize_descriptions.graph_intelligence_strategy import (
                run_graph_intelligence,
            )

            return run_graph_intelligence
        case _:
            msg = f"Unknown strategy: {strategy_type}"
            raise ValueError(msg)
