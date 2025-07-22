# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_graph_intelligence,  run_resolve_entities and _create_text_list_splitter methods to run graph intelligence."""

import logging

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.index.operations.summarize_descriptions.description_summary_extractor import (
    SummarizeExtractor,
)
from graphrag.index.operations.summarize_descriptions.typing import (
    StrategyConfig,
    SummarizedDescriptionResult,
)
from graphrag.language_model.manager import ModelManager
from graphrag.language_model.protocol.base import ChatModel

logger = logging.getLogger(__name__)


async def run_graph_intelligence(
    id: str | tuple[str, str],
    descriptions: list[str],
    cache: PipelineCache,
    args: StrategyConfig,
) -> SummarizedDescriptionResult:
    """Run the graph intelligence entity extraction strategy."""
    llm_config = LanguageModelConfig(**args["llm"])
    llm = ModelManager().get_or_create_chat_model(
        name="summarize_descriptions",
        model_type=llm_config.type,
        config=llm_config,
        cache=cache,
    )

    return await run_summarize_descriptions(llm, id, descriptions, args)


async def run_summarize_descriptions(
    model: ChatModel,
    id: str | tuple[str, str],
    descriptions: list[str],
    args: StrategyConfig,
) -> SummarizedDescriptionResult:
    """Run the entity extraction chain."""
    # Extraction Arguments
    summarize_prompt = args.get("summarize_prompt", None)
    max_input_tokens = args["max_input_tokens"]
    max_summary_length = args["max_summary_length"]
    extractor = SummarizeExtractor(
        model_invoker=model,
        summarization_prompt=summarize_prompt,
        on_error=lambda e, stack, details: logger.error(
            "Entity Extraction Error",
            exc_info=e,
            extra={"stack": stack, "details": details},
        ),
        max_summary_length=max_summary_length,
        max_input_tokens=max_input_tokens,
    )

    result = await extractor(id=id, descriptions=descriptions)
    return SummarizedDescriptionResult(id=result.id, description=result.description)
