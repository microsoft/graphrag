# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Rate limit middleware."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphrag_llm.rate_limit import RateLimiter
    from graphrag_llm.tokenizer import Tokenizer
    from graphrag_llm.types import (
        AsyncLLMFunction,
        LLMFunction,
    )


def with_rate_limiting(
    *,
    sync_middleware: "LLMFunction",
    async_middleware: "AsyncLLMFunction",
    rate_limiter: "RateLimiter",
    tokenizer: "Tokenizer",
) -> tuple[
    "LLMFunction",
    "AsyncLLMFunction",
]:
    """Wrap model functions with rate limit middleware.

    Args
    ----
        sync_middleware: LLMFunction
            The synchronous model function to wrap.
            Either a completion function or an embedding function.
        async_middleware: AsyncLLMFunction
            The asynchronous model function to wrap.
            Either a completion function or an embedding function.
        rate_limiter: RateLimiter
            The rate limiter to use.
        tokenizer: Tokenizer
            The tokenizer to use for counting tokens.

    Returns
    -------
        tuple[LLMFunction, AsyncLLMFunction]
            The synchronous and asynchronous model functions wrapped with rate limit middleware.
    """

    def _rate_limit_middleware(
        **kwargs: Any,
    ):
        token_count = int(
            kwargs.get("max_tokens") or kwargs.get("max_completion_tokens") or 0
        )
        messages = kwargs.get("messages")  # completion call
        input: list[str] | None = kwargs.get("input")  # embedding call
        if messages:
            token_count += tokenizer.num_prompt_tokens(messages=messages)
        elif input:
            token_count += sum(tokenizer.num_tokens(text) for text in input)

        with rate_limiter.acquire(token_count):
            return sync_middleware(**kwargs)

    async def _rate_limit_middleware_async(
        **kwargs: Any,
    ):
        token_count = int(
            kwargs.get("max_tokens") or kwargs.get("max_completion_tokens") or 0
        )
        messages = kwargs.get("messages")  # completion call
        input = kwargs.get("input")  # embedding call
        if messages:
            token_count += tokenizer.num_prompt_tokens(messages=messages)
        elif input:
            token_count += sum(tokenizer.num_tokens(text) for text in input)
        with rate_limiter.acquire(token_count):
            return await async_middleware(**kwargs)

    return (_rate_limit_middleware, _rate_limit_middleware_async)  # type: ignore
