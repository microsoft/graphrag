# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""LLM Parameters model."""

from typing_extensions import NotRequired, TypedDict


class ParallelizationParametersInputModel(TypedDict):
    """LLM Parameters model."""

    stagger: NotRequired[float | str | None]
    num_threads: NotRequired[int | str | None]
