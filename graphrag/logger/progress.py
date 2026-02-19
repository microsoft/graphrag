# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Progress Logging Utilities."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass
class Progress:
    """A class representing the progress of a task."""

    description: str | None = None
    """Description of the progress"""

    total_items: int | None = None
    """Total number of items"""

    completed_items: int | None = None
    """Number of items completed"""


ProgressHandler = Callable[[Progress], None]
"""A function to handle progress reports."""


def progress_iterable(
    iterable: Iterable[T],
    progress: ProgressHandler | None,
    num_total: int | None = None,
    description: str = "",
) -> Iterable[T]:
    """Wrap an iterable with a progress handler. Every time an item is yielded, the progress handler will be called with the current progress."""
    if num_total is None:
        num_total = len(list(iterable))

    for item in iterable:
        yield item
