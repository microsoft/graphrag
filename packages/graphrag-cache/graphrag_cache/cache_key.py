# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Create cache key."""

from typing import Any, Protocol, runtime_checkable

from graphrag_common.hasher import hash_data


@runtime_checkable
class CacheKeyCreator(Protocol):
    """Create cache key function protocol.

    Args
    ----
        input_args: dict[str, Any]
            The input arguments for creating the cache key.

    Returns
    -------
        str
            The generated cache key.
    """

    def __call__(
        self,
        input_args: dict[str, Any],
    ) -> str:
        """Create cache key."""
        ...


def create_cache_key(input_args: dict[str, Any]) -> str:
    """Create a cache key based on the input arguments."""
    return hash_data(input_args)
