# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A class to interact with the cache."""

import json
from typing import Generic, TypeVar

from typing_extensions import Unpack

from graphrag.llm.types import LLM, LLMCache, LLMInput, LLMOutput, OnCacheActionFn

from ._create_cache_key import create_hash_key

# If there's a breaking change in what we cache, we should increment this version number to invalidate existing caches
_cache_strategy_version = 2

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


def _noop_cache_fn(_k: str, _v: str | None):
    pass


class CachingLLM(LLM[TIn, TOut], Generic[TIn, TOut]):
    """A class to interact with the cache."""

    _cache: LLMCache
    _delegate: LLM[TIn, TOut]
    _operation: str
    _llm_parameters: dict
    _on_cache_hit: OnCacheActionFn
    _on_cache_miss: OnCacheActionFn

    def __init__(
        self,
        delegate: LLM[TIn, TOut],
        llm_parameters: dict,
        operation: str,
        cache: LLMCache,
    ):
        self._delegate = delegate
        self._llm_parameters = llm_parameters
        self._cache = cache
        self._operation = operation
        self._on_cache_hit = _noop_cache_fn
        self._on_cache_miss = _noop_cache_fn

    def set_delegate(self, delegate: LLM[TIn, TOut]) -> None:
        """Set the delegate LLM. (for testing)."""
        self._delegate = delegate

    def on_cache_hit(self, fn: OnCacheActionFn | None) -> None:
        """Set the function to call when a cache hit occurs."""
        self._on_cache_hit = fn or _noop_cache_fn

    def on_cache_miss(self, fn: OnCacheActionFn | None) -> None:
        """Set the function to call when a cache miss occurs."""
        self._on_cache_miss = fn or _noop_cache_fn

    def _cache_key(
        self, input: TIn, name: str | None, args: dict, history: list[dict] | None
    ) -> str:
        json_input = json.dumps(input)
        tag = (
            f"{name}-{self._operation}-v{_cache_strategy_version}"
            if name is not None
            else self._operation
        )
        return create_hash_key(tag, json_input, args, history)

    async def __call__(
        self,
        input: TIn,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[TOut]:
        """Execute the LLM."""
        # Check for an Existing cache item
        name = kwargs.get("name")
        history_in = kwargs.get("history") or None
        llm_args = {**self._llm_parameters, **(kwargs.get("model_parameters") or {})}
        cache_key = self._cache_key(input, name, llm_args, history_in)
        cached_result = await self._cache.get(cache_key)

        if cached_result:
            self._on_cache_hit(cache_key, name)
            return LLMOutput(
                output=cached_result,
            )

        # Report the Cache Miss
        self._on_cache_miss(cache_key, name)

        # Compute the new result
        result = await self._delegate(input, **kwargs)

        # Cache the new result
        if result.output is not None:
            await self._cache.set(
                cache_key,
                result.output,
                {
                    "input": input,
                    "parameters": llm_args,
                    "history": history_in,
                },
            )
        return result
