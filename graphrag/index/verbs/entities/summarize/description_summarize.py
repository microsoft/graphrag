# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the summarize_descriptions verb."""

import asyncio
import logging
from enum import Enum
from typing import Any, NamedTuple, cast

import networkx as nx
import pandas as pd
from datashaper import (
    ProgressTicker,
    TableContainer,
    VerbCallbacks,
    VerbInput,
    progress_ticker,
    verb,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.utils import load_graph

from .strategies.typing import SummarizationStrategy

log = logging.getLogger(__name__)


class DescriptionSummarizeRow(NamedTuple):
    """DescriptionSummarizeRow class definition."""

    graph: Any


class SummarizeStrategyType(str, Enum):
    """SummarizeStrategyType class definition."""

    graph_intelligence = "graph_intelligence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


@verb(name="summarize_descriptions")
async def summarize_descriptions(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    column: str,
    to: str,
    strategy: dict[str, Any] | None = None,
    **kwargs,
) -> TableContainer:
    """
    Summarize entity and relationship descriptions from an entity graph.

    ## Usage

    To turn this feature ON please set the environment variable `GRAPHRAG_SUMMARIZE_DESCRIPTIONS_ENABLED=True`.

    ### json

    ```json
    {
        "verb": "",
        "args": {
            "column": "the_document_text_column_to_extract_descriptions_from", /* Required: This will be a graphml graph in string form which represents the entities and their relationships */
            "to": "the_column_to_output_the_summarized_descriptions_to", /* Required: This will be a graphml graph in string form which represents the entities and their relationships after being summarized */
            "strategy": {...} <strategy_config>, see strategies section below
        }
    }
    ```

    ### yaml

    ```yaml
    verb: entity_extract
    args:
        column: the_document_text_column_to_extract_descriptions_from
        to: the_column_to_output_the_summarized_descriptions_to
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
    output = cast(pd.DataFrame, input.get_input())
    strategy = strategy or {}
    strategy_exec = load_strategy(
        strategy.get("type", SummarizeStrategyType.graph_intelligence)
    )
    strategy_config = {**strategy}

    async def get_resolved_entities(row, semaphore: asyncio.Semaphore):
        graph: nx.Graph = load_graph(cast(str | nx.Graph, getattr(row, column)))

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

        return DescriptionSummarizeRow(
            graph="\n".join(nx.generate_graphml(graph)),
        )

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

    # Graph is always on row 0, so here a derive from rows does not work
    # This iteration will only happen once, but avoids hardcoding a iloc[0]
    # Since parallelization is at graph level (nodes and edges), we can't use
    # the parallelization of the derive_from_rows
    semaphore = asyncio.Semaphore(kwargs.get("num_threads", 4))

    results = [
        await get_resolved_entities(row, semaphore) for row in output.itertuples()
    ]

    to_result = []

    for result in results:
        if result:
            to_result.append(result.graph)
        else:
            to_result.append(None)
    output[to] = to_result
    return TableContainer(table=output)


def load_strategy(strategy_type: SummarizeStrategyType) -> SummarizationStrategy:
    """Load strategy method definition."""
    match strategy_type:
        case SummarizeStrategyType.graph_intelligence:
            from .strategies.graph_intelligence import run as run_gi

            return run_gi
        case _:
            msg = f"Unknown strategy: {strategy_type}"
            raise ValueError(msg)
