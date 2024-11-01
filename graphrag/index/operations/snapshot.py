# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing snapshot method definition."""

import pandas as pd

from graphrag.index.storage.pipeline_storage import PipelineStorage


async def snapshot(
    input: pd.DataFrame,
    name: str,
    formats: list[str],
    storage: PipelineStorage,
) -> None:
    """Take a entire snapshot of the tabular data."""
    for fmt in formats:
        if fmt == "parquet":
            await storage.set(f"{name}.parquet", input.to_parquet())
        elif fmt == "json":
            await storage.set(
                f"{name}.json", input.to_json(orient="records", lines=True)
            )
