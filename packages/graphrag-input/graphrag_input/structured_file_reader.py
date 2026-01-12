# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'StructuredFileReader' model."""

import logging
from typing import Any

from graphrag_input.get_property import get_property
from graphrag_input.hashing import gen_sha512_hash
from graphrag_input.input_reader import InputReader
from graphrag_input.text_document import TextDocument

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
        rows: list[dict[str, Any]],
        path: str,
    ) -> list[TextDocument]:
        """Process configured data columns from a list of loaded dicts."""
        documents = []
        for index, row in enumerate(rows):
            # text column is required - harvest from dict
            text = get_property(row, self._text_column)
            # id is optional - harvest from dict or hash from text
            id = (
                get_property(row, self._id_column)
                if self._id_column
                else gen_sha512_hash({"text": text}, ["text"])
            )
            # title is optional - harvest from dict or use filename
            num = f" ({index})" if len(rows) > 1 else ""
            title = (
                get_property(row, self._title_column)
                if self._title_column
                else f"{path}{num}"
            )
            creation_date = await self._storage.get_creation_date(path)
            documents.append(
                TextDocument(
                    id=id,
                    title=title,
                    text=text,
                    creation_date=creation_date,
                    raw_data=row,
                )
            )
        return documents
