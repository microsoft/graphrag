# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.
# Author Khaled Alam <khaledalam.net@gmail.com>

"""Module for estimating costs of processing and indexing data using language models."""

import sys
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.index.input.factory import create_input
from graphrag.index.text_splitting.text_splitting import TokenTextSplitter
from graphrag.index.utils.is_null import is_null
from graphrag.logger.base import ProgressLogger
from graphrag.logger.factory import LoggerFactory
from graphrag.logger.types import LoggerType


PRICING_URL = "https://raw.githubusercontent.com/khaledalam/openapi-pricing/refs/heads/master/pricing.json"
_cached_pricing = None
CENTS_TO_DOLLARS = 0.01


class InvalidInputTypeError(TypeError):
    """Raised when input_docs is not a DataFrame."""


def load_pricing(
    progress_logger: ProgressLogger,
) -> tuple[any, any] | tuple[dict, dict]:
    """Load and cache pricing data for models and embeddings from the pricing URL."""
    global _cached_pricing

    if _cached_pricing is not None:
        return _cached_pricing

    try:
        import requests

        response = requests.get(PRICING_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        _cached_pricing = (data.get("models", {}), data.get("embedding", {}))
    except Exception as _:
        progress_logger.exception("Failed to fetch pricing")
        return {}, {}

    return _cached_pricing


def count_tokens(
    texts: list,
    model_config: LanguageModelConfig,
    chunk_size: int = 1200,
    chunk_overlap: int = 100,
) -> int:
    """Count the total number of tokens in the given texts using the specified model configuration."""
    splitter = TokenTextSplitter(
        encoding_name=model_config.encoding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return sum(splitter.num_tokens(t) for t in texts if t.strip())


def estimate_cost(
    config: GraphRagConfig,
    input_chunks: list,
    progress_logger: ProgressLogger,
    average_output_tokens_per_chunk: int = 500,
) -> dict | None:
    """Calculate the estimated cost of processing input chunks using configured models."""
    if is_null(input_chunks):
        progress_logger.info("No input provided.")
        return None

    model_pricing, embedding_pricing = load_pricing(progress_logger)

    embed_config = config.models["default_embedding_model"]
    chat_config = config.models["default_chat_model"]
    embed_model_name = embed_config.model
    chat_model_name = chat_config.model

    texts = [
        chunk.get("text", "") if isinstance(chunk, dict) else chunk
        for chunk in input_chunks
    ]

    chunk_config = getattr(config, "chunking", None)
    chunk_size = chunk_config.chunk_size if chunk_config else 1200
    chunk_overlap = chunk_config.chunk_overlap if chunk_config else 100

    total_embedding_tokens = count_tokens(
        texts, embed_config, chunk_size, chunk_overlap
    )
    prompt_wrapped_texts = [f"<prompt>\n{t}" for t in texts]
    total_chat_input_tokens = count_tokens(
        prompt_wrapped_texts, chat_config, chunk_size, chunk_overlap
    )

    total_chat_output_tokens = len(texts) * average_output_tokens_per_chunk

    embed_price_per_1k = embedding_pricing.get(
        embed_model_name, model_pricing.get(embed_model_name, {}).get("input", 0)
    )
    embed_cost = (total_embedding_tokens / 1000) * (embed_price_per_1k / 100)

    if chat_model_name not in model_pricing:
        fallback = "gpt-4-turbo"
        progress_logger.info(
            f"'{chat_model_name}' not found in pricing. Falling back to '{fallback}'."
        )
        chat_model_name = fallback

    chat_price = model_pricing.get(chat_model_name, {})
    chat_input_price = chat_price.get("input", 0) * CENTS_TO_DOLLARS
    chat_output_price = chat_price.get("output", 0) * CENTS_TO_DOLLARS

    chat_cost = (total_chat_input_tokens / 1000) * chat_input_price + (
        total_chat_output_tokens / 1000
    ) * chat_output_price

    total_tokens = (
        total_embedding_tokens + total_chat_input_tokens + total_chat_output_tokens
    )
    total_requests = len(texts)
    total_cost = embed_cost + chat_cost

    return {
        "embedding_model": embed_model_name,
        "embedding_tokens": total_embedding_tokens,
        "embedding_cost": embed_cost,
        "chat_model": chat_model_name,
        "chat_input_tokens": total_chat_input_tokens,
        "chat_output_tokens": total_chat_output_tokens,
        "chat_cost": chat_cost,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "total_requests": total_requests,
        "average_output_tokens_per_chunk": average_output_tokens_per_chunk,
        "chunks_count": len(input_chunks),
    }


def estimate_cost_flow(
    config: GraphRagConfig,
    logger_type: LoggerType,
    average_output_tokens_per_chunk: int = 500,
) -> None:
    """Process input data and estimate costs for the entire indexing flow."""
    progress_logger = LoggerFactory().create_logger(logger_type)

    import nest_asyncio

    nest_asyncio.apply()

    async def load_input(config):
        """Load input data asynchronously based on the provided configuration."""
        return await create_input(config.input, None, config.root_dir)

    try:
        import asyncio

        input_docs = asyncio.get_event_loop().run_until_complete(load_input(config))
    except RuntimeError as e:
        progress_logger.info("estimate_cost_flow: Async error: ", e)

    chunk_config = getattr(config, "chunking", None)
    chunk_size = chunk_config.chunk_size if chunk_config else 1200
    chunk_overlap = chunk_config.chunk_overlap if chunk_config else 100

    splitter = TokenTextSplitter(
        encoding_name=config.models["default_embedding_model"].encoding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = []
    total_token_count = 0

    import pandas as pd

    if isinstance(input_docs, pd.DataFrame):
        for i, row in input_docs.iterrows():
            try:
                content = row.get("text")
                if content and isinstance(content, str):
                    content_chunks = splitter.split_text(content)
                    for _, chunk in enumerate(content_chunks):
                        tokens = splitter.num_tokens(chunk)
                        total_token_count += tokens
                        chunks.append(chunk)
            except Exception as e:
                progress_logger.exception(
                    f"estimate_cost_flow: Error processing row {i + 1}: {e}"
                )
    else:
        msg = f"Expected DataFrame from input_docs, got {type(input_docs)}"
        raise InvalidInputTypeError(msg)

    result = estimate_cost(
        config, chunks, progress_logger, average_output_tokens_per_chunk
    )
    print_cost_report(result, progress_logger)
    ask_continue_indexing(progress_logger)


def ask_continue_indexing(progress_logger: ProgressLogger) -> None:
    """Prompt user to confirm whether to proceed with full indexing after cost estimation."""
    progress_logger.info(f"\n{'=' * 55}")
    progress_logger.info("Estimated cost completed.")
    progress_logger.info("Do you want to continue and run the actual indexing?")
    progress_logger.info("  - [y] Yes")
    progress_logger.info("  - [n] No (default)")
    progress_logger.info(f"\n{'=' * 55}")

    confirm = input("Your choice [y/N]: ").strip().lower()
    if confirm != "y":
        progress_logger.error("Indexing cancelled by user.")
        sys.exit(0)
    progress_logger.success("Proceeding with full indexing...\n")


def print_cost_report(result: dict, progress_logger: ProgressLogger) -> None:
    """Print a formatted report of the cost estimation results."""
    progress_logger.success("Approximate LLM Token and Cost Estimation Summary:\n")
    progress_logger.info(
        f"- Average output tokens per chunk: {result['average_output_tokens_per_chunk']} - Chunks count: {result['chunks_count']}\n"
    )
    progress_logger.info(f"- Embedding Model: {result['embedding_model']}")
    progress_logger.info(
        f"  Tokens: {result['embedding_tokens']} → ${result['embedding_cost']:.4f}\n"
    )
    progress_logger.info(f"- Chat Model: {result['chat_model']}")
    progress_logger.info(f"  Input Tokens: {result['chat_input_tokens']}")
    progress_logger.info(
        f"  Output Tokens (estimated): {result['chat_output_tokens']} → ${result['chat_cost']:.4f}\n"
    )
    progress_logger.info(f"TOTAL ESTIMATED: ${result['total_cost']:.4f}")
    progress_logger.info(f"Total Tokens: {result['total_tokens']}")
    progress_logger.info(f"Total Requests: {result['total_requests']}")
    progress_logger.warning(
        " Note: This estimate is based on the --average-output-tokens-per-chunk value and may not reflect the exact final cost. Actual usage may vary depending on model behavior and content structure. This provides a conservative upper-bound estimate."
    )
