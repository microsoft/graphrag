# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'InputReader' model."""

from __future__ import annotations

import logging
import re
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphrag_storage import Storage

    from graphrag_input.text_document import TextDocument

logger = logging.getLogger(__name__)


class InputReader(metaclass=ABCMeta):
    """Provide a cache interface for the pipeline."""

    def __init__(
        self,
        storage: Storage,
        encoding: str = "utf-8",
        file_pattern: str | None = None,
        **kwargs,
    ):
        self._storage = storage
        self._encoding = encoding
        self._file_pattern = file_pattern

    async def read_files(self) -> list[TextDocument]:
        """Load files from storage and apply a loader function based on file type. Process metadata on the results if needed."""
        files = list(self._storage.find(re.compile(self._file_pattern)))
        if len(files) == 0:
            msg = f"No {self._file_pattern} matches found in storage"
            logger.warning(msg)
            files = []

        documents: list[TextDocument] = []

        for file in files:
            try:
                documents.extend(await self.read_file(file))
            except Exception as e:  # noqa: BLE001 (catching Exception is fine here)
                logger.warning("Warning! Error loading file %s. Skipping...", file)
                logger.warning("Error: %s", e)

        logger.info(
            "Found %d %s files, loading %d",
            len(files),
            self._file_pattern,
            len(documents),
        )
        total_files_log = (
            f"Total number of unfiltered {self._file_pattern} rows: {len(documents)}"
        )
        logger.info(total_files_log)

        return documents

    @abstractmethod
    async def read_file(self, path: str) -> list[TextDocument]:
        """Read a file into a list of documents.

        Args:
            - path - The path to read the file from.

        Returns
        -------
            - output - List with an entry for each document in the file.
        """
