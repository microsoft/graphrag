# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired, TypedDict


class EmbedGraphConfigInput(TypedDict):
    """The default configuration section for Node2Vec."""

    enabled: NotRequired[bool | str | None]
    num_walks: NotRequired[int | str | None]
    walk_length: NotRequired[int | str | None]
    window_size: NotRequired[int | str | None]
    iterations: NotRequired[int | str | None]
    random_seed: NotRequired[int | str | None]
    strategy: NotRequired[dict | None]
