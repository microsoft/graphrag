# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Table Emitter Factories."""

from graphrag.config.models.graphdb_config import GraphDBConfig
from graphrag.common.storage import PipelineStorage
from graphrag.index.typing import ErrorHandlerFn

from .csv_table_emitter import CSVTableEmitter
from .json_table_emitter import JsonTableEmitter
from .parquet_table_emitter import ParquetTableEmitter
from .graph_db_emitter import GraphDBEmitter
from .table_emitter import TableEmitter
from .types import TableEmitterType

def create_table_emitter(
    emitter_type: TableEmitterType, storage: PipelineStorage, on_error: ErrorHandlerFn, graphdb_params: GraphDBConfig|None = None
) -> TableEmitter:
    """Create a table emitter based on the specified type."""
    match emitter_type:
        case TableEmitterType.Json:
            return JsonTableEmitter(storage)
        case TableEmitterType.Parquet:
            return ParquetTableEmitter(storage, on_error)
        case TableEmitterType.CSV:
            return CSVTableEmitter(storage)
        case TableEmitterType.Graphdb:
            return GraphDBEmitter(graphdb_params)
        case _:
            msg = f"Unsupported table emitter type: {emitter_type}"
            raise ValueError(msg)


def create_table_emitters(
    emitter_types: list[TableEmitterType],
    storage: PipelineStorage,
    on_error: ErrorHandlerFn,
    graphdb_params: GraphDBConfig|None = None,
) -> list[TableEmitter]:
    """Create a list of table emitters based on the specified types."""
    return [
        create_table_emitter(emitter_type, storage, on_error, graphdb_params)
        for emitter_type in emitter_types
    ]
