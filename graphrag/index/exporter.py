# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""ParquetExporter module."""

import logging
import traceback

import pandas as pd
from pyarrow.lib import ArrowInvalid, ArrowTypeError

from graphrag.index.typing import ErrorHandlerFn
from graphrag.storage.pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)


class ParquetExporter:
    """ParquetExporter class.

    A class that exports dataframe's to a storage destination in .parquet file format.
    """

    _storage: PipelineStorage
    _on_error: ErrorHandlerFn

    def __init__(
        self,
        storage: PipelineStorage,
        on_error: ErrorHandlerFn,
    ):
        """Create a new Parquet Table TableExporter."""
        self._storage = storage
        self._on_error = on_error

    async def export(self, name: str, data: pd.DataFrame) -> None:
        """Export dataframe to storage."""
        filename = f"{name}.parquet"
        log.info("exporting parquet table %s", filename)
        try:
            await self._storage.set(filename, data.to_parquet())
        except ArrowTypeError as e:
            log.exception("Error while exporting parquet table")
            self._on_error(
                e,
                traceback.format_exc(),
                None,
            )
        except ArrowInvalid as e:
            log.exception("Error while exporting parquet table")
            self._on_error(
                e,
                traceback.format_exc(),
                None,
            )
