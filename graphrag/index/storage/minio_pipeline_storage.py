# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Minio Blob Storage implementation of PipelineStorage."""
import io
import logging
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datashaper import Progress
from minio import Minio
from minio.error import S3Error

from graphrag.index.progress import ProgressReporter

from .typing import PipelineStorage

log = logging.getLogger(__name__)

class MinioPipelineStorage(PipelineStorage):
    """The MinIO-Storage implementation."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False,
        encoding: str | None = None,
        path_prefix: str | None = None,
    ):
        """Create a new MinIOStorage instance."""
        self._minio_client = Minio(
            endpoint, access_key=access_key, secret_key=secret_key, secure=secure
        )
        self._encoding = encoding or "utf-8"
        self._bucket_name = bucket_name
        self._path_prefix = path_prefix or ""
        self.create_bucket()
        self.access_key = access_key
        self.endpoint = endpoint
        self.secret_key = secret_key
        self.secure = secure

    def create_bucket(self) -> None:
        """Create the bucket if it does not exist."""
        if not self.bucket_exists():
            self._minio_client.make_bucket(self._bucket_name)

    def delete_bucket(self) -> None:
        """Delete the bucket."""
        if self.bucket_exists():
            self._minio_client.remove_bucket(self._bucket_name)

    def bucket_exists(self) -> bool:
        """Check if the bucket exists."""
        return self._minio_client.bucket_exists(self._bucket_name)

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressReporter | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find objects in a bucket using a file pattern, as well as a custom filter function."""

        base_dir = base_dir or ""

        log.info(
            "search bucket %s for files matching %s",
            self._bucket_name,
            file_pattern.pattern,
        )

        def objectname(object_name: str) -> str:
            if object_name.startswith(self._path_prefix):
                object_name = object_name.replace(self._path_prefix, "", 1)
            if object_name.startswith("/"):
                object_name = object_name[1:]
            return object_name

        def item_filter(item: dict[str, Any]) -> bool:
            if file_filter is None:
                return True

            return all(re.match(value, item[key]) for key, value in file_filter.items())

        try:
            all_objects = list(self._minio_client.list_objects(self._bucket_name, base_dir, recursive=True))

            num_loaded = 0
            num_total = len(all_objects)
            num_filtered = 0
            for obj in all_objects:
                match = file_pattern.match(obj.object_name) # type: ignore
                if match:
                    group = match.groupdict()
                    if item_filter(group):
                        yield (objectname(obj.object_name), group) # type: ignore
                        num_loaded += 1
                        if max_count > 0 and num_loaded >= max_count:
                            break
                    else:
                        num_filtered += 1
                else:
                    num_filtered += 1
                if progress is not None:
                    progress(
                        _create_progress_status(num_loaded, num_filtered, num_total)
                    )
        except Exception:
            log.exception(
                "Error finding objects: base_dir=%s, file_pattern=%s, file_filter=%s",
                base_dir,
                file_pattern,
                file_filter,
            )
            raise

    async def get(
        self, key: str, as_bytes: bool | None = False, encoding: str | None = None
    ) -> Any:
        """Get a value from the storage."""
        try:
            key = self._keyname(key)
            response = self._minio_client.get_object(self._bucket_name, key)
            data = response.read()
            response.close()
            response.release_conn()
            if not as_bytes:
                coding = encoding or "utf-8"
                data = data.decode(coding)
        except Exception:
            log.exception("Error getting key %s", key)
            return None
        else:
            return data

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set a value in the storage."""
        try:
            print("aaaaaaaa")
            print(self._path_prefix)
            key = self._keyname(key)
            print("bbbbbbbbbb")
            if isinstance(value, bytes):
                data = value
            else:
                coding = encoding or "utf-8"
                data = value.encode(coding)
              
            # self._minio_client.put_object(
            #     self._bucket_name, key, data, length=len(data) # type: ignore
            # )
            binary_io_data = io.BytesIO(data)
            self._minio_client.put_object(
                self._bucket_name,
                object_name=key,
                data=binary_io_data,
                length=len(data),
                content_type="application/json"
            )
        except Exception:
            log.exception("Error setting key %s: %s", key)

    async def has(self, key: str) -> bool:
        """Check if a key exists in the storage."""
        key = self._keyname(key)
        try:
            self._minio_client.stat_object(self._bucket_name, key)
            return True
        except S3Error:
            return False

    async def delete(self, key: str) -> None:
        """Delete a key from the storage."""
        key = self._keyname(key)
        self._minio_client.remove_object(self._bucket_name, key)

    async def clear(self) -> None:
        """Clear the storage."""
        all_objects = list(self._minio_client.list_objects(self._bucket_name, recursive=True))
        for obj in all_objects:
            self._minio_client.remove_object(self._bucket_name, obj.object_name) # type: ignore

    def child(self, name: str | None) -> "PipelineStorage":
        """Create a child storage instance."""
        if name is None:
            return self
        path = str(Path(self._path_prefix) / name)
        return MinioPipelineStorage(
            self.endpoint,
            self.access_key,
            self.secret_key,
            self._bucket_name,
            secure=self.secure,
            encoding=self._encoding,
            path_prefix=path,
        )

    def _keyname(self, key: str) -> str:
        """Get the key name."""
        time = f"{datetime.now(tz=timezone.utc).strftime('%Y-%m-%d-%H:%M:%S:%f')}"
        self._path_prefix = self._path_prefix.replace("${timestamp}",time)
        object_name = f"{self._path_prefix}"
        return str(Path(object_name) / key)

def create_minio_storage(
    endpoint: str,
    access_key: str,
    secret_key: str,
    bucket_name: str,
    base_dir: str | None = None,
    secure: bool = True
) -> PipelineStorage:
    """Create a MinIO based storage."""
    log.info("Creating MinIO storage at %s", bucket_name)
    if bucket_name is None:
        error_message = "No bucket name provided for MinIO storage."
        raise ValueError(error_message)
    return MinioPipelineStorage(
        endpoint, access_key, secret_key, bucket_name, False, path_prefix=base_dir
    )

def validate_bucket_name(bucket_name: str):
    """
    Check if the provided bucket name is valid based on MinIO rules.
    
    MinIO follows the same bucket naming rules as AWS S3.
    """
    # Check the length of the name
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        return ValueError(
            f"Bucket name must be between 3 and 63 characters in length. Name provided was {len(bucket_name)} characters long."
        )

    # Check if the name starts with a letter or number
    if not bucket_name[0].isalnum():
        return ValueError(
            f"Bucket name must start with a letter or number. Starting character was {bucket_name[0]}."
        )

    # Check for valid characters (letters, numbers, hyphen) and lowercase letters
    if not re.match("^[a-z0-9-]+$", bucket_name):
        return ValueError(
            f"Bucket name must only contain:\n- lowercase letters\n- numbers\n- or hyphens\nName provided was {bucket_name}."
        )

    # Check for consecutive hyphens
    if "--" in bucket_name:
        return ValueError(
            f"Bucket name cannot contain consecutive hyphens. Name provided was {bucket_name}."
        )

    # Check for hyphens at the end of the name
    if bucket_name[-1] == "-":
        return ValueError(
            f"Bucket name cannot end with a hyphen. Name provided was {bucket_name}."
        )

    return True

def _create_progress_status(
    num_loaded: int, num_filtered: int, num_total: int
) -> Progress:
    return Progress(
        total_items=num_total,
        completed_items=num_loaded + num_filtered,
        description=f"{num_loaded} files loaded ({num_filtered} filtered)",
    )