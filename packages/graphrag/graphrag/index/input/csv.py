# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'CSVFileReader' model."""

import logging
from io import BytesIO

import pandas as pd

from graphrag.index.input.structured_file_reader import StructuredFileReader

logger = logging.getLogger(__name__)


class CSVFileReader(StructuredFileReader):
    """Reader implementation for csv files."""

    async def read_file(self, path: str) -> pd.DataFrame:
        """Read a csv file into a DataFrame of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - DataFrame with a row for each document in the file.
        """
        buffer = BytesIO(await self._storage.get(path, as_bytes=True))
        data = pd.read_csv(buffer, encoding=self._encoding)
        return await self.process_data_columns(data, path)
