# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Apply a generic transform function to each row in a table."""

import asyncio
import inspect
import logging
import traceback
from collections.abc import Awaitable, Callable, Coroutine, Hashable
from typing import Any, TypeVar, cast

import pandas as pd

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.logger.progress import progress_ticker

logger = logging.getLogger(__name__)
ItemType = TypeVar("ItemType")


class ParallelizationError(ValueError):
    """Exception for invalid parallel processing."""

    def __init__(self, num_errors: int, example: str | None = None):
        msg = f"{num_errors} Errors occurred while running parallel transformation, could not complete!"
        if example:
            msg += f"\nExample error: {example}"
        super().__init__(msg)


async def derive_from_rows(
    input: pd.DataFrame,
    transform: Callable[[pd.Series], Awaitable[ItemType]],
    callbacks: WorkflowCallbacks | None = None,
    num_threads: int = 4,
    async_type: AsyncType = AsyncType.AsyncIO,
) -> list[ItemType | None]:
    """Apply a generic transform function to each row. Any errors will be reported and thrown."""
    callbacks = callbacks or NoopWorkflowCallbacks()
    match async_type:
        case AsyncType.AsyncIO:
            return await derive_from_rows_asyncio(
                input, transform, callbacks, num_threads
            )
        case AsyncType.Threaded:
            return await derive_from_rows_asyncio_threads(
                input, transform, callbacks, num_threads
            )
        case _:
            msg = f"Unsupported scheduling type {async_type}"
            raise ValueError(msg)


"""A module containing the derive_from_rows_async method."""


async def derive_from_rows_asyncio_threads(
    input: pd.DataFrame,
    transform: Callable[[pd.Series], Awaitable[ItemType]],
    callbacks: WorkflowCallbacks,
    num_threads: int | None = 4,
) -> list[ItemType | None]:
    """
    Derive from rows asynchronously.

    This is useful for IO bound operations.
    """
    semaphore = asyncio.Semaphore(num_threads or 4)

    async def gather(execute: ExecuteFn[ItemType]) -> list[ItemType | None]:
        tasks = [asyncio.to_thread(execute, row) for row in input.iterrows()]

        async def execute_task(task: Coroutine) -> ItemType | None:
            async with semaphore:
                # fire off the thread
                thread = await task
                return await thread

        return await asyncio.gather(*[execute_task(task) for task in tasks])

    return await _derive_from_rows_base(input, transform, callbacks, gather)


"""A module containing the derive_from_rows_async method."""


async def derive_from_rows_asyncio(
    input: pd.DataFrame,
    transform: Callable[[pd.Series], Awaitable[ItemType]],
    callbacks: WorkflowCallbacks,
    num_threads: int = 4,
) -> list[ItemType | None]:
    """
    Derive from rows asynchronously.

    This is useful for IO bound operations.
    """
    semaphore = asyncio.Semaphore(num_threads or 4)

    async def gather(execute: ExecuteFn[ItemType]) -> list[ItemType | None]:
        async def execute_row_protected(
            row: tuple[Hashable, pd.Series],
        ) -> ItemType | None:
            async with semaphore:
                return await execute(row)

        tasks = [
            asyncio.create_task(execute_row_protected(row)) for row in input.iterrows()
        ]
        return await asyncio.gather(*tasks)

    return await _derive_from_rows_base(input, transform, callbacks, gather)


ItemType = TypeVar("ItemType")

ExecuteFn = Callable[[tuple[Hashable, pd.Series]], Awaitable[ItemType | None]]
GatherFn = Callable[[ExecuteFn], Awaitable[list[ItemType | None]]]


async def _derive_from_rows_base(
    input: pd.DataFrame,
    transform: Callable[[pd.Series], Awaitable[ItemType]],
    callbacks: WorkflowCallbacks,
    gather: GatherFn[ItemType],
) -> list[ItemType | None]:
    """
    Derive from rows asynchronously.

    This is useful for IO bound operations.
    """
    tick = progress_ticker(callbacks.progress, num_total=len(input))
    errors: list[tuple[BaseException, str]] = []

    async def execute(row: tuple[Any, pd.Series]) -> ItemType | None:
        try:
            result = transform(row[1])
            if inspect.iscoroutine(result):
                result = await result
        except Exception as e:  # noqa: BLE001
            errors.append((e, traceback.format_exc()))
            return None
        else:
            return cast("ItemType", result)
        finally:
            tick(1)

    result = await gather(execute)

    tick.done()

    for error, stack in errors:
        callbacks.error("parallel transformation error", error, stack)

    if len(errors) > 0:
        raise ParallelizationError(len(errors), errors[0][1])

    return result
