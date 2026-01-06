# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'CSVFileReader' model."""

import logging

import pandas as pd

from graphrag.index.input.input_reader import InputReader
from graphrag.index.utils.hashing import gen_sha512_hash

logger = logging.getLogger(__name__)


class StructuredFileReader(InputReader):
    """Base reader implementation for structured files such as csv and json."""

    def __init__(
        self,
        id_column: str | None = None,
        title_column: str | None = None,
        text_column: str = "text",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._id_column = id_column
        self._title_column = title_column
        self._text_column = text_column

    async def process_data_columns(
        self,
        documents: pd.DataFrame,
        path: str,
    ) -> pd.DataFrame:
        """Process configured data columns of a DataFrame."""
        # id is optional - generate from harvest from df or hash from text
        if self._id_column is not None:
            documents["id"] = documents.apply(lambda x: x[self._id_column], axis=1)
        else:
            documents["id"] = documents.apply(
                lambda x: gen_sha512_hash(x, x.keys()), axis=1
            )

        # title is optional - harvest from df or use filename
        if self._title_column is not None:
            documents["title"] = documents.apply(
                lambda x: x[self._title_column], axis=1
            )
        else:
            documents["title"] = documents.apply(lambda _: path, axis=1)

        # text column is required - harvest from df
        documents["text"] = documents.apply(lambda x: x[self._text_column], axis=1)

        creation_date = await self._storage.get_creation_date(path)
        documents["creation_date"] = documents.apply(lambda _: creation_date, axis=1)

        return documents
