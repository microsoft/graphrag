# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_gi,  run_resolve_entities and _create_text_list_splitter methods to run graph intelligence."""

from datashaper import VerbCallbacks

from graphrag.config.enums import LLMType
from graphrag.index.cache import PipelineCache
from graphrag.index.graph.extractors.summarize import SummarizeExtractor
from graphrag.index.llm import load_llm
from graphrag.index.verbs.entities.summarize.strategies.typing import (
    StrategyConfig,
    SummarizedDescriptionResult,
)
from graphrag.llm import CompletionLLM

from .defaults import DEFAULT_LLM_CONFIG


async def run(
    described_items: str | tuple[str, str],
    descriptions: list[str],
    reporter: VerbCallbacks,
    pipeline_cache: PipelineCache,
    args: StrategyConfig,
) -> SummarizedDescriptionResult:
    """Run the graph intelligence entity extraction strategy."""
    llm_config = args.get("llm", DEFAULT_LLM_CONFIG)
    llm_type = llm_config.get("type", LLMType.StaticResponse)
    llm = load_llm(
        "summarize_descriptions", llm_type, reporter, pipeline_cache, llm_config
    )
    return await run_summarize_descriptions(
        llm, described_items, descriptions, reporter, args
    )


async def run_summarize_descriptions(
    llm: CompletionLLM,
    items: str | tuple[str, str],
    descriptions: list[str],
    reporter: VerbCallbacks,
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
            reporter.error("Entity Extraction Error", e, stack, details)
            if reporter
            else None
        ),
        max_summary_length=args.get("max_summary_length", None),
        max_input_tokens=max_tokens,
    )

    result = await extractor(items=items, descriptions=descriptions)
    return SummarizedDescriptionResult(
        items=result.items, description=result.description
    )
