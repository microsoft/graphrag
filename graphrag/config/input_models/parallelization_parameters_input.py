# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM Parameters model."""

from typing_extensions import NotRequired, TypedDict


class ParallelizationParametersInput(TypedDict):
    """LLM Parameters model."""

    stagger: NotRequired[float | str | None]
    num_threads: NotRequired[int | str | None]
