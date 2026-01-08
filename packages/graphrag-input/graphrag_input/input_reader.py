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
        file_type: str,
        encoding: str = "utf-8",
        file_pattern: str | None = None,
        **kwargs,
    ):
        self._storage = storage
        self._file_type = file_type
        self._encoding = encoding

        # built-in readers set a default pattern if none is provided
        # this is usually just the file type itself, e.g., the file extension
        pattern = (
            file_pattern if file_pattern is not None else f".*\\.{self._file_type}$"
        )
        if file_pattern is None and self._file_type == "text":
            pattern = ".*\\.txt$"

        self._file_pattern = pattern

    async def read_files(self) -> list[TextDocument]:
        """Load files from storage and apply a loader function based on file type. Process metadata on the results if needed."""
        files = list(self._storage.find(re.compile(self._file_pattern)))
        if len(files) == 0:
            msg = f"No {self._file_type} files found in storage"  # TODO: use a storage __str__ to define it per impl
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
            self._file_type,
            len(documents),
        )
        total_files_log = (
            f"Total number of unfiltered {self._file_type} rows: {len(documents)}"
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
