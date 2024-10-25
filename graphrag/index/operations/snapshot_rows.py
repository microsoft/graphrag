# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'FormatSpecifier' model."""

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from graphrag.index.storage.pipeline_storage import PipelineStorage


@dataclass
class FormatSpecifier:
    """Format specifier class definition."""

    format: str
    extension: str


async def snapshot_rows(
    input: pd.DataFrame,
    column: str | None,
    base_name: str,
    storage: PipelineStorage,
    formats: list[str | dict[str, Any]],
    row_name_column: str | None = None,
) -> None:
    """Take a by-row snapshot of the tabular data."""
    parsed_formats = _parse_formats(formats)
    num_rows = len(input)

    def get_row_name(row: Any, row_idx: Any):
        if row_name_column is None:
            if num_rows == 1:
                return base_name
            return f"{base_name}.{row_idx}"
        return f"{base_name}.{row[row_name_column]}"

    for row_idx, row in input.iterrows():
        for fmt in parsed_formats:
            row_name = get_row_name(row, row_idx)
            extension = fmt.extension
            if fmt.format == "json":
                await storage.set(
                    f"{row_name}.{extension}",
                    (
                        json.dumps(row[column], ensure_ascii=False)
                        if column is not None
                        else json.dumps(row.to_dict(), ensure_ascii=False)
                    ),
                )
            elif fmt.format == "text":
                if column is None:
                    msg = "column must be specified for text format"
                    raise ValueError(msg)
                await storage.set(f"{row_name}.{extension}", str(row[column]))


def _parse_formats(formats: list[str | dict[str, Any]]) -> list[FormatSpecifier]:
    """Parse the formats into a list of FormatSpecifiers."""
    return [
        (
            FormatSpecifier(**fmt)
            if isinstance(fmt, dict)
            else FormatSpecifier(format=fmt, extension=_get_format_extension(fmt))
        )
        for fmt in formats
    ]


def _get_format_extension(fmt: str) -> str:
    """Get the file extension for a given format."""
    if fmt == "json":
        return "json"
    if fmt == "text":
        return "txt"
    if fmt == "parquet":
        return "parquet"
    if fmt == "csv":
        return "csv"
    msg = f"Unknown format: {fmt}"
    raise ValueError(msg)
