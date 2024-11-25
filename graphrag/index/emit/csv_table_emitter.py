# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CSVTableEmitter module."""

import logging

import pandas as pd

from graphrag.index.emit.table_emitter import TableEmitter
from graphrag.index.storage.pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)


class CSVTableEmitter(TableEmitter):
    """CSVTableEmitter class."""

    _storage: PipelineStorage

    def __init__(self, storage: PipelineStorage):
        """Create a new CSV Table Emitter."""
        self._storage = storage

    async def emit(self, name: str, data: pd.DataFrame) -> None:
        """Emit a dataframe to storage."""
        filename = f"{name}.csv"
        log.info("emitting CSV table %s", filename)
        await self._storage.set(
            filename,
            data.to_csv(),
        )
