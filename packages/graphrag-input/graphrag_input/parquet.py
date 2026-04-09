# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'ParquetFileReader' model."""

import io
import logging

import pyarrow.parquet as pq

from graphrag_input.structured_file_reader import StructuredFileReader
from graphrag_input.text_document import TextDocument

logger = logging.getLogger(__name__)


class ParquetFileReader(StructuredFileReader):
    """Reader implementation for parquet files."""

    def __init__(self, file_pattern: str | None = None, **kwargs):
        super().__init__(
            file_pattern=file_pattern if file_pattern is not None else ".*\\.parquet$",
            **kwargs,
        )

    async def read_file(self, path: str) -> list[TextDocument]:
        """Read a parquet file into a list of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - list with a TextDocument for each row in the file.
        """
        file_bytes = await self._storage.get(path, as_bytes=True)
        table = pq.read_table(io.BytesIO(file_bytes))
        rows = table.to_pylist()
        return await self.process_data_columns(rows, path)
