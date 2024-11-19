# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""ParquetTableEmitter module."""

import logging
import traceback

import pandas as pd
from pyarrow.lib import ArrowInvalid, ArrowTypeError

from graphrag.index.emit.table_emitter import TableEmitter
from graphrag.index.storage.pipeline_storage import PipelineStorage
from graphrag.index.typing import ErrorHandlerFn

log = logging.getLogger(__name__)


class ParquetTableEmitter(TableEmitter):
    """ParquetTableEmitter class."""

    _storage: PipelineStorage
    _on_error: ErrorHandlerFn
    extension = "parquet"

    def __init__(
        self,
        storage: PipelineStorage,
        on_error: ErrorHandlerFn,
    ):
        """Create a new Parquet Table Emitter."""
        self._storage = storage
        self._on_error = on_error

    async def emit(self, name: str, data: pd.DataFrame) -> None:
        """Emit a dataframe to storage."""
        filename = f"{name}.{self.extension}"
        log.info("emitting parquet table %s", filename)
        # TODO: refactor to emit the dataframe directly instead of the parquet bytestring
        # TODO: refactor all PipelineStorage implementations to align with this change
        try:
            await self._storage.set(filename, data.to_parquet())
        except ArrowTypeError as e:
            log.exception("Error while emitting parquet table")
            self._on_error(
                e,
                traceback.format_exc(),
                None,
            )
        except ArrowInvalid as e:
            log.exception("Error while emitting parquet table")
            self._on_error(
                e,
                traceback.format_exc(),
                None,
            )
