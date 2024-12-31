# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing snapshot method definition."""

import pandas as pd

from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.storage import write_table_to_storage


async def snapshot(
    input: pd.DataFrame,
    name: str,
    formats: list[str],
    storage: PipelineStorage,
) -> None:
    """Take a entire snapshot of the tabular data."""
    for fmt in formats:
        if fmt == "parquet":
            await write_table_to_storage(input, name, storage)
        elif fmt == "json":
            await storage.set(
                f"{name}.json", input.to_json(orient="records", lines=True)
            )
