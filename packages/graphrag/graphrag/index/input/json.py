# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'JSONFileReader' model."""

import json
import logging

import pandas as pd

from graphrag.index.input.input_reader import InputReader
from graphrag.index.input.util import process_data_columns

logger = logging.getLogger(__name__)


class JSONFileReader(InputReader):
    """Reader implementation for json files."""

    async def read_file(self, path: str) -> pd.DataFrame:
        """Read a JSON file into a DataFrame of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - DataFrame with a row for each document in the file.
        """
        text = await self._storage.get(path, encoding=self._encoding)
        as_json = json.loads(text)
        # json file could just be a single object, or an array of objects
        rows = as_json if isinstance(as_json, list) else [as_json]
        data = pd.DataFrame(rows)
        data = process_data_columns(data, path, self._text_column, self._title_column)
        creation_date = await self._storage.get_creation_date(path)
        data["creation_date"] = data.apply(lambda _: creation_date, axis=1)

        return data
