# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_graph_intelligence,  run_resolve_entities and _create_text_list_splitter methods to run graph intelligence."""

from datashaper import VerbCallbacks

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.graph.extractors.summarize import SummarizeExtractor
from graphrag.index.llm.load_llm import load_llm
from graphrag.index.operations.summarize_descriptions.typing import (
    StrategyConfig,
    SummarizedDescriptionResult,
)
from graphrag.llm import CompletionLLM


async def run_graph_intelligence(
    described_items: str | tuple[str, str],
    descriptions: list[str],
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    args: StrategyConfig,
) -> SummarizedDescriptionResult:
    """Run the graph intelligence entity extraction strategy."""
    llm_config = args.get("llm", {})
    llm_type = llm_config.get("type")
    llm = load_llm("summarize_descriptions", llm_type, callbacks, cache, llm_config)
    return await run_summarize_descriptions(
        llm, described_items, descriptions, callbacks, args
    )


async def run_summarize_descriptions(
    llm: CompletionLLM,
    items: str | tuple[str, str],
    descriptions: list[str],
    callbacks: VerbCallbacks,
    args: StrategyConfig,
) -> SummarizedDescriptionResult:
    """Run the entity extraction chain."""
    # Extraction Arguments
    summarize_prompt = args.get("summarize_prompt", None)
    entity_name_key = args.get("entity_name_key", "entity_name")
    input_descriptions_key = args.get("input_descriptions_key", "description_list")
    max_tokens = args.get("max_tokens", None)

    extractor = SummarizeExtractor(
        llm_invoker=llm,
        summarization_prompt=summarize_prompt,
        entity_name_key=entity_name_key,
        input_descriptions_key=input_descriptions_key,
        on_error=lambda e, stack, details: (
            callbacks.error("Entity Extraction Error", e, stack, details)
            if callbacks
            else None
        ),
        max_summary_length=args.get("max_summary_length", None),
        max_input_tokens=max_tokens,
    )

    result = await extractor(items=items, descriptions=descriptions)
    return SummarizedDescriptionResult(
        items=result.items, description=result.description
    )
