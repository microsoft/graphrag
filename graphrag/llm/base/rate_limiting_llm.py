# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Rate limiting LLM implementation."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)
from typing_extensions import Unpack

from graphrag.llm.errors import RetriesExhaustedError
from graphrag.llm.limiting import LLMLimiter
from graphrag.llm.types import (
    LLM,
    LLMConfig,
    LLMInput,
    LLMInvocationFn,
    LLMInvocationResult,
    LLMOutput,
)

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")
TRateLimitError = TypeVar("TRateLimitError", bound=BaseException)

_CANNOT_MEASURE_INPUT_TOKENS_MSG = "cannot measure input tokens"
_CANNOT_MEASURE_OUTPUT_TOKENS_MSG = "cannot measure output tokens"

log = logging.getLogger(__name__)


class RateLimitingLLM(LLM[TIn, TOut], Generic[TIn, TOut]):
    """A class to interact with the cache."""

    _delegate: LLM[TIn, TOut]
    _rate_limiter: LLMLimiter | None
    _semaphore: asyncio.Semaphore | None
    _count_tokens: Callable[[str], int]
    _config: LLMConfig
    _operation: str
    _retryable_errors: list[type[Exception]]
    _rate_limit_errors: list[type[Exception]]
    _on_invoke: LLMInvocationFn
    _extract_sleep_recommendation: Callable[[Any], float]

    def __init__(
        self,
        delegate: LLM[TIn, TOut],
        config: LLMConfig,
        operation: str,
        retryable_errors: list[type[Exception]],
        rate_limit_errors: list[type[Exception]],
        rate_limiter: LLMLimiter | None = None,
        semaphore: asyncio.Semaphore | None = None,
        count_tokens: Callable[[str], int] | None = None,
        get_sleep_time: Callable[[BaseException], float] | None = None,
    ):
        self._delegate = delegate
        self._rate_limiter = rate_limiter
        self._semaphore = semaphore
        self._config = config
        self._operation = operation
        self._retryable_errors = retryable_errors
        self._rate_limit_errors = rate_limit_errors
        self._count_tokens = count_tokens or (lambda _s: -1)
        self._extract_sleep_recommendation = get_sleep_time or (lambda _e: 0.0)
        self._on_invoke = lambda _v: None

    def on_invoke(self, fn: LLMInvocationFn | None) -> None:
        """Set the on_invoke function."""
        self._on_invoke = fn or (lambda _v: None)

    def count_request_tokens(self, input: TIn) -> int:
        """Count the request tokens on an input request."""
        if isinstance(input, str):
            return self._count_tokens(input)
        if isinstance(input, list):
            result = 0
            for item in input:
                if isinstance(item, str):
                    result += self._count_tokens(item)
                elif isinstance(item, dict):
                    result += self._count_tokens(item.get("content", ""))
                else:
                    raise TypeError(_CANNOT_MEASURE_INPUT_TOKENS_MSG)
            return result
        raise TypeError(_CANNOT_MEASURE_INPUT_TOKENS_MSG)

    def count_response_tokens(self, output: TOut | None) -> int:
        """Count the request tokens on an output response."""
        if output is None:
            return 0
        if isinstance(output, str):
            return self._count_tokens(output)
        if isinstance(output, list) and all(isinstance(x, str) for x in output):
            return sum(self._count_tokens(item) for item in output)
        if isinstance(output, list):
            # Embedding response, don't count it
            return 0
        raise TypeError(_CANNOT_MEASURE_OUTPUT_TOKENS_MSG)

    async def __call__(
        self,
        input: TIn,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[TOut]:
        """Execute the LLM with semaphore & rate limiting."""
        name = kwargs.get("name", "Process")
        attempt_number = 0
        call_times: list[float] = []
        input_tokens = self.count_request_tokens(input)
        max_retries = self._config.max_retries or 10
        max_retry_wait = self._config.max_retry_wait or 10
        follow_recommendation = self._config.sleep_on_rate_limit_recommendation
        retryer = AsyncRetrying(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential_jitter(max=max_retry_wait),
            reraise=True,
            retry=retry_if_exception_type(tuple(self._retryable_errors)),
        )

        async def sleep_for(time: float | None) -> None:
            log.warning(
                "%s failed to invoke LLM %s/%s attempts. Cause: rate limit exceeded, will retry. Recommended sleep for %d seconds. Follow recommendation? %s",
                name,
                attempt_number,
                max_retries,
                time,
                follow_recommendation,
            )
            if follow_recommendation and time:
                await asyncio.sleep(time)
            raise

        async def do_attempt() -> LLMOutput[TOut]:
            nonlocal call_times
            call_start = asyncio.get_event_loop().time()
            try:
                return await self._delegate(input, **kwargs)
            except BaseException as e:
                if isinstance(e, tuple(self._rate_limit_errors)):
                    sleep_time = self._extract_sleep_recommendation(e)
                    await sleep_for(sleep_time)
                raise
            finally:
                call_end = asyncio.get_event_loop().time()
                call_times.append(call_end - call_start)

        async def execute_with_retry() -> tuple[LLMOutput[TOut], float]:
            nonlocal attempt_number
            async for attempt in retryer:
                with attempt:
                    if self._rate_limiter and input_tokens > 0:
                        await self._rate_limiter.acquire(input_tokens)
                    start = asyncio.get_event_loop().time()
                    attempt_number += 1
                    return await do_attempt(), start

            log.error("Retries exhausted for %s", name)
            raise RetriesExhaustedError(name, max_retries)

        result: LLMOutput[TOut]
        start = 0.0

        if self._semaphore is None:
            result, start = await execute_with_retry()
        else:
            async with self._semaphore:
                result, start = await execute_with_retry()

        end = asyncio.get_event_loop().time()
        output_tokens = self.count_response_tokens(result.output)
        if self._rate_limiter and output_tokens > 0:
            await self._rate_limiter.acquire(output_tokens)

        invocation_result = LLMInvocationResult(
            result=result,
            name=name,
            num_retries=attempt_number - 1,
            total_time=end - start,
            call_times=call_times,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        self._handle_invoke_result(invocation_result)
        return result

    def _handle_invoke_result(
        self, result: LLMInvocationResult[LLMOutput[TOut]]
    ) -> None:
        log.info(
            'perf - llm.%s "%s" with %s retries took %s. input_tokens=%d, output_tokens=%d',
            self._operation,
            result.name,
            result.num_retries,
            result.total_time,
            result.input_tokens,
            result.output_tokens,
        )
        self._on_invoke(result)
