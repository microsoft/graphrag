# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Table Emitter Factories."""

from graphrag.index.emit.csv_table_emitter import CSVTableEmitter
from graphrag.index.emit.json_table_emitter import JsonTableEmitter
from graphrag.index.emit.parquet_table_emitter import ParquetTableEmitter
from graphrag.index.emit.table_emitter import TableEmitter
from graphrag.index.emit.types import TableEmitterType
from graphrag.index.storage.pipeline_storage import PipelineStorage
from graphrag.index.typing import ErrorHandlerFn


def create_table_emitter(
    emitter_type: TableEmitterType, storage: PipelineStorage, on_error: ErrorHandlerFn
) -> TableEmitter:
    """Create a table emitter based on the specified type."""
    match emitter_type:
        case TableEmitterType.Json:
            return JsonTableEmitter(storage)
        case TableEmitterType.Parquet:
            return ParquetTableEmitter(storage, on_error)
        case TableEmitterType.CSV:
            return CSVTableEmitter(storage)
        case _:
            msg = f"Unsupported table emitter type: {emitter_type}"
            raise ValueError(msg)


def create_table_emitters(
    emitter_types: list[TableEmitterType],
    storage: PipelineStorage,
    on_error: ErrorHandlerFn,
) -> list[TableEmitter]:
    """Create a list of table emitters based on the specified types."""
    return [
        create_table_emitter(emitter_type, storage, on_error)
        for emitter_type in emitter_types
    ]
