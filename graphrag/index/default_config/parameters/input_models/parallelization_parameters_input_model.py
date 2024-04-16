# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""LLM Parameters model."""

from typing import TypedDict

from typing_extensions import NotRequired


class ParallelizationParametersInputModel(TypedDict):
    """LLM Parameters model."""

    stagger: NotRequired[float | str | None]
    num_threads: NotRequired[int | str | None]
