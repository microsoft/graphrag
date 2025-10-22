# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""File-based Storage implementation of Storage."""

import logging
import os
import re
import shutil
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import aiofiles
from aiofiles.os import remove
from aiofiles.ospath import exists

from graphrag_storage.storage import (
    Storage,
    get_timestamp_formatted_with_local_tz,
)

logger = logging.getLogger(__name__)


class FileStorage(Storage):
    """File storage class definition."""

    _base_dir: Path
    _encoding: str

    def __init__(self, base_dir: str, encoding: str = "utf-8", **kwargs: Any) -> None:
        """Create a file based storage."""
        self._base_dir = Path(base_dir).resolve()
        self._encoding = encoding
        logger.info("Creating file storage at [%s]", self._base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def find(
        self,
        file_pattern: re.Pattern[str],
    ) -> Iterator[str]:
        """Find files in the storage using a file pattern."""
        logger.info(
            "Search [%s] for files matching [%s]", self._base_dir, file_pattern.pattern
        )
        all_files = list(self._base_dir.rglob("**/*"))
        logger.debug("All files and folders: %s", [file.name for file in all_files])
        num_loaded = 0
        num_total = len(all_files)
        num_filtered = 0
        for file in all_files:
            match = file_pattern.search(f"{file}")
            if match:
                filename = f"{file}".replace(str(self._base_dir), "", 1)
                if filename.startswith(os.sep):
                    filename = filename[1:]
                yield filename
                num_loaded += 1
            else:
                num_filtered += 1
        logger.debug(
            "Files loaded: %d, filtered: %d, total: %d",
            num_loaded,
            num_filtered,
            num_total,
        )

    async def get(
        self, key: str, as_bytes: bool | None = False, encoding: str | None = None
    ) -> Any:
        """Get method definition."""
        file_path = _join_path(self._base_dir, key)

        if await self.has(key):
            return await self._read_file(file_path, as_bytes, encoding)

        return None

    async def _read_file(
        self,
        path: str | Path,
        as_bytes: bool | None = False,
        encoding: str | None = None,
    ) -> Any:
        """Read the contents of a file."""
        read_type = "rb" if as_bytes else "r"
        encoding = None if as_bytes else (encoding or self._encoding)

        async with aiofiles.open(
            path,
            cast("Any", read_type),
            encoding=encoding,
        ) as f:
            return await f.read()

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set method definition."""
        is_bytes = isinstance(value, bytes)
        write_type = "wb" if is_bytes else "w"
        encoding = None if is_bytes else encoding or self._encoding
        async with aiofiles.open(
            _join_path(self._base_dir, key),
            cast("Any", write_type),
            encoding=encoding,
        ) as f:
            await f.write(value)

    async def has(self, key: str) -> bool:
        """Has method definition."""
        return await exists(_join_path(self._base_dir, key))

    async def delete(self, key: str) -> None:
        """Delete method definition."""
        if await self.has(key):
            await remove(_join_path(self._base_dir, key))

    async def clear(self) -> None:
        """Clear method definition."""
        for file in self._base_dir.glob("*"):
            if file.is_dir():
                shutil.rmtree(file)
            else:
                file.unlink()

    def child(self, name: str | None) -> "Storage":
        """Create a child storage instance."""
        if name is None:
            return self
        child_path = str(self._base_dir / name)
        return FileStorage(base_dir=child_path, encoding=self._encoding)

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        return [item.name for item in self._base_dir.iterdir() if item.is_file()]

    async def get_creation_date(self, key: str) -> str:
        """Get the creation date of a file."""
        file_path = _join_path(self._base_dir, key)

        creation_timestamp = file_path.stat().st_ctime
        creation_time_utc = datetime.fromtimestamp(creation_timestamp, tz=timezone.utc)

        return get_timestamp_formatted_with_local_tz(creation_time_utc)


def _join_path(file_path: Path, file_name: str) -> Path:
    """Join a path and a file. Independent of the OS."""
    return (file_path / Path(file_name).parent / Path(file_name).name).resolve()
