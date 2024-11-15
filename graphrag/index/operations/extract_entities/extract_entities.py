# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing entity_extract methods."""

import logging
from enum import Enum
from typing import Any

import networkx as nx
import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
    derive_from_rows,
)

from graphrag.index.bootstrap import bootstrap
from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.extract_entities.strategies.typing import (
    Document,
    EntityExtractStrategy,
)

log = logging.getLogger(__name__)


class ExtractEntityStrategyType(str, Enum):
    """ExtractEntityStrategyType class definition."""

    graph_intelligence = "graph_intelligence"
    graph_intelligence_json = "graph_intelligence_json"
    nltk = "nltk"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]


async def extract_entities(
    input: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    text_column: str,
    id_column: str,
    to: str,
    strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types=DEFAULT_ENTITY_TYPES,
    num_threads: int = 4,
) -> tuple[pd.DataFrame, list[nx.Graph]]:
    """
    Extract entities from a piece of text.

    ## Usage
    ```yaml
    args:
        column: the_document_text_column_to_extract_entities_from
        id_column: the_column_with_the_unique_id_for_each_row
        to: the_column_to_output_the_entities_to
        strategy: <strategy_config>, see strategies section below
        summarize_descriptions: true | false /* Optional: This will summarize the descriptions of the entities and relationships, default: true */
        entity_types:
            - list
            - of
            - entity
            - types
            - to
            - extract
    ```

    ## Strategies
    The entity extract verb uses a strategy to extract entities from a document. The strategy is a json object which defines the strategy to use. The following strategies are available:

    ### graph_intelligence
    This strategy uses the [graph_intelligence] library to extract entities from a document. In particular it uses a LLM to extract entities from a piece of text. The strategy config is as follows:

    ```yml
    strategy:
        type: graph_intelligence
        extraction_prompt: !include ./entity_extraction_prompt.txt # Optional, the prompt to use for extraction
        completion_delimiter: "<|COMPLETE|>" # Optional, the delimiter to use for the LLM to mark completion
        tuple_delimiter: "<|>" # Optional, the delimiter to use for the LLM to mark a tuple
        record_delimiter: "##" # Optional, the delimiter to use for the LLM to mark a record

        prechunked: true | false # Optional, If the document is already chunked beforehand, otherwise this will chunk the document into smaller bits. default: false
        encoding_name: cl100k_base # Optional, The encoding to use for the LLM, if not already prechunked, default: cl100k_base
        chunk_size: 1000 # Optional ,The chunk size to use for the LLM, if not already prechunked, default: 1200
        chunk_overlap: 100 # Optional, The chunk overlap to use for the LLM, if not already prechunked, default: 100

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

    ### nltk
    This strategy uses the [nltk] library to extract entities from a document. In particular it uses a nltk to extract entities from a piece of text. The strategy config is as follows:
    ```yml
    strategy:
        type: nltk
    ```
    """
    log.debug("entity_extract strategy=%s", strategy)
    if entity_types is None:
        entity_types = DEFAULT_ENTITY_TYPES
    strategy = strategy or {}
    strategy_exec = _load_strategy(
        strategy.get("type", ExtractEntityStrategyType.graph_intelligence)
    )
    strategy_config = {**strategy}

    num_started = 0

    async def run_strategy(row):
        nonlocal num_started
        text = row[text_column]
        id = row[id_column]
        result = await strategy_exec(
            [Document(text=text, id=id)],
            entity_types,
            callbacks,
            cache,
            strategy_config,
        )
        num_started += 1
        return [result.entities, result.graph]

    results = await derive_from_rows(
        input,
        run_strategy,
        callbacks,
        scheduling_type=async_mode,
        num_threads=num_threads,
    )

    to_result = []
    graphs = []
    for result in results:
        if result:
            to_result.append(result[0])
            graphs.append(result[1])
        else:
            to_result.append(None)
            graphs.append(None)

    input[to] = to_result

    return (input.reset_index(drop=True), graphs)


def _load_strategy(strategy_type: ExtractEntityStrategyType) -> EntityExtractStrategy:
    """Load strategy method definition."""
    match strategy_type:
        case ExtractEntityStrategyType.graph_intelligence:
            from graphrag.index.operations.extract_entities.strategies.graph_intelligence import (
                run_graph_intelligence,
            )

            return run_graph_intelligence

        case ExtractEntityStrategyType.nltk:
            bootstrap()
            # dynamically import nltk strategy to avoid dependency if not used
            from graphrag.index.operations.extract_entities.strategies.nltk import (
                run as run_nltk,
            )

            return run_nltk
        case _:
            msg = f"Unknown strategy: {strategy_type}"
            raise ValueError(msg)
