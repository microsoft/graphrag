# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing snapshot method definition."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from graphrag.index.storage import PipelineStorage


@verb(name="snapshot")
async def snapshot(
    input: VerbInput,
    name: str,
    formats: list[str],
    storage: PipelineStorage,
    **_kwargs: dict,
) -> TableContainer:
    """Take a entire snapshot of the tabular data."""
    source = cast(pd.DataFrame, input.get_input())

    await snapshot_df(source, name, formats, storage)

    return TableContainer(table=source)


async def snapshot_df(
    input: pd.DataFrame,
    name: str,
    formats: list[str],
    storage: PipelineStorage,
) -> None:
    """Take a entire snapshot of the tabular data."""
    for fmt in formats:
        if fmt == "parquet":
            await storage.set(name + ".parquet", input.to_parquet())
        elif fmt == "json":
            await storage.set(
                name + ".json", input.to_json(orient="records", lines=True)
            )
