# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'FormatSpecifier' model."""

import json
from pathlib import Path
from typing import Any, cast

from datashaper import TableContainer, VerbInput, verb
from pandas.core.frame import DataFrame
from pandas.core.groupby import DataFrameGroupBy

from graphrag.index.storage import PipelineStorage
from graphrag.index.verbs.snapshot_rows import _parse_formats


@verb(name="restore_snapshot_rows")
async def restore_snapshot_rows(
    input: VerbInput,
    column: str,
    to: str,
    storage: PipelineStorage,
    formats: list[str | dict[str, Any]],
    **_kwargs: dict,
) -> TableContainer:
    """Take a by-row snapshot of the tabular data."""
    if isinstance(input.get_input(), DataFrameGroupBy):
        msg = "Cannot snapshot rows of a grouped DataFrame"
        raise TypeError(msg)
    
    data = cast(DataFrame, input.get_input())
    parsed_formats = _parse_formats(formats)
    
    if to not in data.columns:
        # init the table column where the snapshot content will be stored
        data[to] = None

    # do not modify the original data
    new_data = data.copy()
    new_data[column] = None

    for row_idx, row in data.iterrows():
        # for each row, load only the data in the specified formats
        for fmt in parsed_formats:
            row_name = Path(row[column])
            if row_name.suffix != fmt.extension:
                continue

            filename = row_name.name
            data_bytes:bytes|bytearray = await storage.get(filename, as_bytes=True)
            
            if fmt.format == "json":
                new_data[row_idx, column] = json.loads(data_bytes)
            elif fmt.format == "text":
                new_data[row_idx, column] = data_bytes.decode("utf-8")
            else:
                msg = f"Unsupported format: {fmt.format}"
                raise ValueError(msg)
    
    return TableContainer(table=data.dropna(subset=[column]))
