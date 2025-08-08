# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""File-based Storage implementation of PipelineStorage."""

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

from graphrag.storage.pipeline_storage import (
    PipelineStorage,
    get_timestamp_formatted_with_local_tz,
)

logger = logging.getLogger(__name__)


class FilePipelineStorage(PipelineStorage):
    """File storage class definition."""

    _root_dir: str
    _encoding: str

    def __init__(self, **kwargs: Any) -> None:
        """Create a file based storage."""
        self._root_dir = kwargs.get("base_dir", "")
        self._encoding = kwargs.get("encoding", "utf-8")
        logger.info("Creating file storage at %s", self._root_dir)
        Path(self._root_dir).mkdir(parents=True, exist_ok=True)

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find files in the storage using a file pattern, as well as a custom filter function."""

        def item_filter(item: dict[str, Any]) -> bool:
            if file_filter is None:
                return True
            return all(
                re.search(value, item[key]) for key, value in file_filter.items()
            )

        search_path = Path(self._root_dir) / (base_dir or "")
        logger.info(
            "search %s for files matching %s", search_path, file_pattern.pattern
        )
        all_files = list(search_path.rglob("**/*"))
        num_loaded = 0
        num_total = len(all_files)
        num_filtered = 0
        for file in all_files:
            match = file_pattern.search(f"{file}")
            if match:
                group = match.groupdict()
                if item_filter(group):
                    filename = f"{file}".replace(self._root_dir, "")
                    if filename.startswith(os.sep):
                        filename = filename[1:]
                    yield (filename, group)
                    num_loaded += 1
                    if max_count > 0 and num_loaded >= max_count:
                        break
                else:
                    num_filtered += 1
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
        file_path = join_path(self._root_dir, key)

        if await self.has(key):
            return await self._read_file(file_path, as_bytes, encoding)
        if await exists(key):
            # Lookup for key, as it is pressumably a new file loaded from inputs
            # and not yet written to storage
            return await self._read_file(key, as_bytes, encoding)

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
            join_path(self._root_dir, key),
            cast("Any", write_type),
            encoding=encoding,
        ) as f:
            await f.write(value)

    async def has(self, key: str) -> bool:
        """Has method definition."""
        return await exists(join_path(self._root_dir, key))

    async def delete(self, key: str) -> None:
        """Delete method definition."""
        if await self.has(key):
            await remove(join_path(self._root_dir, key))

    async def clear(self) -> None:
        """Clear method definition."""
        for file in Path(self._root_dir).glob("*"):
            if file.is_dir():
                shutil.rmtree(file)
            else:
                file.unlink()

    def child(self, name: str | None) -> "PipelineStorage":
        """Create a child storage instance."""
        if name is None:
            return self
        child_path = str(Path(self._root_dir) / Path(name))
        return FilePipelineStorage(base_dir=child_path, encoding=self._encoding)

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        return [item.name for item in Path(self._root_dir).iterdir() if item.is_file()]

    async def get_creation_date(self, key: str) -> str:
        """Get the creation date of a file."""
        file_path = Path(join_path(self._root_dir, key))

        creation_timestamp = file_path.stat().st_ctime
        creation_time_utc = datetime.fromtimestamp(creation_timestamp, tz=timezone.utc)

        return get_timestamp_formatted_with_local_tz(creation_time_utc)


def join_path(file_path: str, file_name: str) -> Path:
    """Join a path and a file. Independent of the OS."""
    return Path(file_path) / Path(file_name).parent / Path(file_name).name
