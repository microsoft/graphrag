# Copyright (c) 2024 Microsoft Corporation.

"""LLM Parameters model."""

from typing_extensions import NotRequired, TypedDict


class ParallelizationParametersInput(TypedDict):
    """LLM Parameters model."""

    stagger: NotRequired[float | str | None]
    num_threads: NotRequired[int | str | None]
