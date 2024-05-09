# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""JsonTableEmitter module."""

import logging

import pandas as pd

from graphrag.index.storage import PipelineStorage

from .table_emitter import TableEmitter

log = logging.getLogger(__name__)


class JsonTableEmitter(TableEmitter):
    """JsonTableEmitter class."""

    _storage: PipelineStorage

    def __init__(self, storage: PipelineStorage):
        """Create a new Json Table Emitter."""
        self._storage = storage

    async def emit(self, name: str, data: pd.DataFrame) -> None:
        """Emit a dataframe to storage."""
        filename = f"{name}.json"

        log.info("emitting JSON table %s", filename)
        await self._storage.set(
            filename,
            data.to_json(orient="records", lines=True, force_ascii=False),
        )
