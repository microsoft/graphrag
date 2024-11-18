# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure Blob Storage implementation of PipelineStorage."""

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from datashaper import Progress

from graphrag.index.storage.pipeline_storage import PipelineStorage
from graphrag.logging.base import ProgressReporter

log = logging.getLogger(__name__)


class BlobPipelineStorage(PipelineStorage):
    """The Blob-Storage implementation."""

    _connection_string: str | None
    _container_name: str
    _path_prefix: str
    _encoding: str
    _storage_account_blob_url: str | None

    def __init__(
        self,
        connection_string: str | None,
        container_name: str,
        encoding: str | None = None,
        path_prefix: str | None = None,
        storage_account_blob_url: str | None = None,
    ):
        """Create a new BlobStorage instance."""
        if connection_string:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
        else:
            if storage_account_blob_url is None:
                msg = "Either connection_string or storage_account_blob_url must be provided."
                raise ValueError(msg)

            self._blob_service_client = BlobServiceClient(
                account_url=storage_account_blob_url,
                credential=DefaultAzureCredential(),
            )
        self._encoding = encoding or "utf-8"
        self._container_name = container_name
        self._connection_string = connection_string
        self._path_prefix = path_prefix or ""
        self._storage_account_blob_url = storage_account_blob_url
        self._storage_account_name = (
            storage_account_blob_url.split("//")[1].split(".")[0]
            if storage_account_blob_url
            else None
        )
        log.info(
            "creating blob storage at container=%s, path=%s",
            self._container_name,
            self._path_prefix,
        )
        self.create_container()

    def create_container(self) -> None:
        """Create the container if it does not exist."""
        if not self.container_exists():
            container_name = self._container_name
            container_names = [
                container.name
                for container in self._blob_service_client.list_containers()
            ]
            if container_name not in container_names:
                self._blob_service_client.create_container(container_name)

    def delete_container(self) -> None:
        """Delete the container."""
        if self.container_exists():
            self._blob_service_client.delete_container(self._container_name)

    def container_exists(self) -> bool:
        """Check if the container exists."""
        container_name = self._container_name
        container_names = [
            container.name for container in self._blob_service_client.list_containers()
        ]
        return container_name in container_names

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressReporter | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find blobs in a container using a file pattern, as well as a custom filter function.

        Params:
            base_dir: The name of the base container.
            file_pattern: The file pattern to use.
            file_filter: A dictionary of key-value pairs to filter the blobs.
            max_count: The maximum number of blobs to return. If -1, all blobs are returned.

        Returns
        -------
                An iterator of blob names and their corresponding regex matches.
        """
        base_dir = base_dir or ""

        log.info(
            "search container %s for files matching %s",
            self._container_name,
            file_pattern.pattern,
        )

        def blobname(blob_name: str) -> str:
            if blob_name.startswith(self._path_prefix):
                blob_name = blob_name.replace(self._path_prefix, "", 1)
            if blob_name.startswith("/"):
                blob_name = blob_name[1:]
            return blob_name

        def item_filter(item: dict[str, Any]) -> bool:
            if file_filter is None:
                return True

            return all(re.match(value, item[key]) for key, value in file_filter.items())

        try:
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            all_blobs = list(container_client.list_blobs())

            num_loaded = 0
            num_total = len(list(all_blobs))
            num_filtered = 0
            for blob in all_blobs:
                match = file_pattern.match(blob.name)
                if match and blob.name.startswith(base_dir):
                    group = match.groupdict()
                    if item_filter(group):
                        yield (blobname(blob.name), group)
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
                "Error finding blobs: base_dir=%s, file_pattern=%s, file_filter=%s",
                base_dir,
                file_pattern,
                file_filter,
            )
            raise

    async def get(
        self, key: str, as_bytes: bool | None = False, encoding: str | None = None
    ) -> Any:
        """Get a value from the cache."""
        try:
            key = self._keyname(key)
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            blob_client = container_client.get_blob_client(key)
            blob_data = blob_client.download_blob().readall()
            if not as_bytes:
                coding = encoding or "utf-8"
                blob_data = blob_data.decode(coding)
        except Exception:
            log.exception("Error getting key %s", key)
            return None
        else:
            return blob_data

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set a value in the cache."""
        try:
            key = self._keyname(key)
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            blob_client = container_client.get_blob_client(key)
            if isinstance(value, bytes):
                blob_client.upload_blob(value, overwrite=True)
            else:
                coding = encoding or "utf-8"
                blob_client.upload_blob(value.encode(coding), overwrite=True)
        except Exception:
            log.exception("Error setting key %s: %s", key)

    def set_df_json(self, key: str, dataframe: Any) -> None:
        """Set a json dataframe."""
        if self._connection_string is None and self._storage_account_name:
            dataframe.to_json(
                self._abfs_url(key),
                storage_options={
                    "account_name": self._storage_account_name,
                    "credential": DefaultAzureCredential(),
                },
                orient="records",
                lines=True,
                force_ascii=False,
            )
        else:
            dataframe.to_json(
                self._abfs_url(key),
                storage_options={"connection_string": self._connection_string},
                orient="records",
                lines=True,
                force_ascii=False,
            )

    def set_df_parquet(self, key: str, dataframe: Any) -> None:
        """Set a parquet dataframe."""
        if self._connection_string is None and self._storage_account_name:
            dataframe.to_parquet(
                self._abfs_url(key),
                storage_options={
                    "account_name": self._storage_account_name,
                    "credential": DefaultAzureCredential(),
                },
            )
        else:
            dataframe.to_parquet(
                self._abfs_url(key),
                storage_options={"connection_string": self._connection_string},
            )

    async def has(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        key = self._keyname(key)
        container_client = self._blob_service_client.get_container_client(
            self._container_name
        )
        blob_client = container_client.get_blob_client(key)
        return blob_client.exists()

    async def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        key = self._keyname(key)
        container_client = self._blob_service_client.get_container_client(
            self._container_name
        )
        blob_client = container_client.get_blob_client(key)
        blob_client.delete_blob()

    async def clear(self) -> None:
        """Clear the cache."""

    def child(self, name: str | None) -> "PipelineStorage":
        """Create a child storage instance."""
        if name is None:
            return self
        path = str(Path(self._path_prefix) / name)
        return BlobPipelineStorage(
            self._connection_string,
            self._container_name,
            self._encoding,
            path,
            self._storage_account_blob_url,
        )

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        msg = "Blob storage does yet not support listing keys."
        raise NotImplementedError(msg)

    def _keyname(self, key: str) -> str:
        """Get the key name."""
        return str(Path(self._path_prefix) / key)

    def _abfs_url(self, key: str) -> str:
        """Get the ABFS URL."""
        path = str(Path(self._container_name) / self._path_prefix / key)
        return f"abfs://{path}"


def create_blob_storage(
    connection_string: str | None,
    storage_account_blob_url: str | None,
    container_name: str,
    base_dir: str | None,
) -> PipelineStorage:
    """Create a blob based storage."""
    log.info("Creating blob storage at %s", container_name)
    if container_name is None:
        msg = "No container name provided for blob storage."
        raise ValueError(msg)
    if connection_string is None and storage_account_blob_url is None:
        msg = "No storage account blob url provided for blob storage."
        raise ValueError(msg)
    return BlobPipelineStorage(
        connection_string,
        container_name,
        path_prefix=base_dir,
        storage_account_blob_url=storage_account_blob_url,
    )


def validate_blob_container_name(container_name: str):
    """
    Check if the provided blob container name is valid based on Azure rules.

        - A blob container name must be between 3 and 63 characters in length.
        - Start with a letter or number
        - All letters used in blob container names must be lowercase.
        - Contain only letters, numbers, or the hyphen.
        - Consecutive hyphens are not permitted.
        - Cannot end with a hyphen.

    Args:
    -----
    container_name (str)
        The blob container name to be validated.

    Returns
    -------
        bool: True if valid, False otherwise.
    """
    # Check the length of the name
    if len(container_name) < 3 or len(container_name) > 63:
        return ValueError(
            f"Container name must be between 3 and 63 characters in length. Name provided was {len(container_name)} characters long."
        )

    # Check if the name starts with a letter or number
    if not container_name[0].isalnum():
        return ValueError(
            f"Container name must start with a letter or number. Starting character was {container_name[0]}."
        )

    # Check for valid characters (letters, numbers, hyphen) and lowercase letters
    if not re.match("^[a-z0-9-]+$", container_name):
        return ValueError(
            f"Container name must only contain:\n- lowercase letters\n- numbers\n- or hyphens\nName provided was {container_name}."
        )

    # Check for consecutive hyphens
    if "--" in container_name:
        return ValueError(
            f"Container name cannot contain consecutive hyphens. Name provided was {container_name}."
        )

    # Check for hyphens at the end of the name
    if container_name[-1] == "-":
        return ValueError(
            f"Container name cannot end with a hyphen. Name provided was {container_name}."
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
