#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing snapshot method definition."""
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
    data = input.get_input()

    for fmt in formats:
        if fmt == "parquet":
            await storage.set(name + ".parquet", data.to_parquet())
        elif fmt == "json":
            await storage.set(
                name + ".json", data.to_json(orient="records", lines=True)
            )

    return TableContainer(table=data)
