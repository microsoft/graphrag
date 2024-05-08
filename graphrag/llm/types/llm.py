# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM Types."""

from typing import Generic, Protocol, TypeVar

from typing_extensions import Unpack

from .llm_io import (
    LLMInput,
    LLMOutput,
)

TIn = TypeVar("TIn", contravariant=True)
TOut = TypeVar("TOut")


class LLM(Protocol, Generic[TIn, TOut]):
    """LLM Protocol definition."""

    async def __call__(
        self,
        input: TIn,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[TOut]:
        """Invoke the LLM, treating the LLM as a function."""
        ...
