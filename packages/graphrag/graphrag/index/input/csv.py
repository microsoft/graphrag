# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'CSVFileReader' model."""

import logging
from io import BytesIO

import pandas as pd

from graphrag.index.input.input_reader import InputReader
from graphrag.index.input.util import process_data_columns

logger = logging.getLogger(__name__)


class CSVFileReader(InputReader):
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
        data = pd.read_csv(buffer, encoding=self._config.encoding)
        data = process_data_columns(data, self._config, path)
        creation_date = await self._storage.get_creation_date(path)
        data["creation_date"] = data.apply(lambda _: creation_date, axis=1)
        return data
