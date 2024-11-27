# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the summarize_descriptions verb."""

import asyncio
import logging
from typing import Any

import networkx as nx
from datashaper import (
    ProgressTicker,
    VerbCallbacks,
    progress_ticker,
)

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.summarize_descriptions.typing import (
    SummarizationStrategy,
    SummarizeStrategyType,
)

log = logging.getLogger(__name__)


async def summarize_descriptions(
    input: nx.Graph,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    strategy: dict[str, Any] | None = None,
    num_threads: int = 4,
) -> nx.Graph:
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

    async def get_resolved_entities(graph: nx.Graph, semaphore: asyncio.Semaphore):
        ticker_length = len(graph.nodes) + len(graph.edges)

        ticker = progress_ticker(callbacks.progress, ticker_length)

        futures = [
            do_summarize_descriptions(
                node,
                sorted(set(graph.nodes[node].get("description", "").split("\n"))),
                ticker,
                semaphore,
            )
            for node in graph.nodes()
        ]
        futures += [
            do_summarize_descriptions(
                edge,
                sorted(set(graph.edges[edge].get("description", "").split("\n"))),
                ticker,
                semaphore,
            )
            for edge in graph.edges()
        ]

        results = await asyncio.gather(*futures)

        for result in results:
            graph_item = result.items
            if isinstance(graph_item, str) and graph_item in graph.nodes():
                graph.nodes[graph_item]["description"] = result.description
            elif isinstance(graph_item, tuple) and graph_item in graph.edges():
                graph.edges[graph_item]["description"] = result.description

        return graph

    async def do_summarize_descriptions(
        graph_item: str | tuple[str, str],
        descriptions: list[str],
        ticker: ProgressTicker,
        semaphore: asyncio.Semaphore,
    ):
        async with semaphore:
            results = await strategy_exec(
                graph_item,
                descriptions,
                callbacks,
                cache,
                strategy_config,
            )
            ticker(1)
        return results

    semaphore = asyncio.Semaphore(num_threads)

    return await get_resolved_entities(input, semaphore)


def load_strategy(strategy_type: SummarizeStrategyType) -> SummarizationStrategy:
    """Load strategy method definition."""
    match strategy_type:
        case SummarizeStrategyType.graph_intelligence:
            from graphrag.index.operations.summarize_descriptions.strategies import (
                run_graph_intelligence,
            )

            return run_graph_intelligence
        case _:
            msg = f"Unknown strategy: {strategy_type}"
            raise ValueError(msg)
