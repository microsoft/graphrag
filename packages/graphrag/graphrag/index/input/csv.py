# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'CSVFileReader' model."""

import csv
import logging

from graphrag.index.input.structured_file_reader import StructuredFileReader
from graphrag.index.input.text_document import TextDocument

logger = logging.getLogger(__name__)


class CSVFileReader(StructuredFileReader):
    """Reader implementation for csv files."""

    async def read_file(self, path: str) -> list[TextDocument]:
        """Read a csv file into a DataFrame of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - DataFrame with a row for each document in the file.
        """
        file = await self._storage.get(path)

        reader = csv.DictReader(file.splitlines())
        return await self.process_data_columns(list(reader), path)
