# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure Blob Storage implementation of Storage."""

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from graphrag_storage.storage import (
    Storage,
    get_timestamp_formatted_with_local_tz,
)

logger = logging.getLogger(__name__)


class AzureBlobStorage(Storage):
    """The Blob-Storage implementation."""

    _connection_string: str | None
    _container_name: str
    _base_dir: str | None
    _encoding: str
    _account_url: str | None
    _blob_service_client: BlobServiceClient
    _storage_account_name: str | None

    def __init__(
        self,
        container_name: str,
        account_url: str | None = None,
        connection_string: str | None = None,
        base_dir: str | None = None,
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> None:
        """Create a new BlobStorage instance."""
        if connection_string is not None and account_url is not None:
            msg = "AzureBlobStorage requires only one of connection_string or account_url to be specified, not both."
            logger.error(msg)
            raise ValueError(msg)

        _validate_blob_container_name(container_name)

        logger.info(
            "Creating blob storage at [%s] and base_dir [%s]",
            container_name,
            base_dir,
        )
        if connection_string:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
        elif account_url:
            self._blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=DefaultAzureCredential(),
            )
        else:
            msg = "AzureBlobStorage requires either a connection_string or account_url to be specified."
            logger.error(msg)
            raise ValueError(msg)

        self._encoding = encoding
        self._container_name = container_name
        self._connection_string = connection_string
        self._base_dir = base_dir
        self._account_url = account_url
        self._storage_account_name = (
            account_url.split("//")[1].split(".")[0] if account_url else None
        )
        self._create_container()

    def _create_container(self) -> None:
        """Create the container if it does not exist."""
        if not self._container_exists():
            container_name = self._container_name
            container_names = [
                container.name
                for container in self._blob_service_client.list_containers()
            ]
            if container_name not in container_names:
                logger.debug("Creating new container [%s]", container_name)
                self._blob_service_client.create_container(container_name)

    def _delete_container(self) -> None:
        """Delete the container."""
        if self._container_exists():
            self._blob_service_client.delete_container(self._container_name)

    def _container_exists(self) -> bool:
        """Check if the container exists."""
        container_name = self._container_name
        container_names = [
            container.name for container in self._blob_service_client.list_containers()
        ]
        return container_name in container_names

    def find(
        self,
        file_pattern: re.Pattern[str],
    ) -> Iterator[str]:
        """Find blobs in a container using a file pattern.

        Params:
            file_pattern: The file pattern to use.

        Returns
        -------
                An iterator of blob names and their corresponding regex matches.
        """
        logger.info(
            "Search container [%s] in base_dir [%s] for files matching [%s]",
            self._container_name,
            self._base_dir,
            file_pattern.pattern,
        )

        def _blobname(blob_name: str) -> str:
            if self._base_dir and blob_name.startswith(self._base_dir):
                blob_name = blob_name.replace(self._base_dir, "", 1)
            if blob_name.startswith("/"):
                blob_name = blob_name[1:]
            return blob_name

        try:
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            all_blobs = list(container_client.list_blobs(self._base_dir))
            logger.debug("All blobs: %s", [blob.name for blob in all_blobs])
            num_loaded = 0
            num_total = len(list(all_blobs))
            num_filtered = 0
            for blob in all_blobs:
                match = file_pattern.search(blob.name)
                if match:
                    yield _blobname(blob.name)
                    num_loaded += 1
                else:
                    num_filtered += 1
            logger.debug(
                "Blobs loaded: %d, filtered: %d, total: %d",
                num_loaded,
                num_filtered,
                num_total,
            )
        except Exception:  # noqa: BLE001
            logger.warning(
                "Error finding blobs: base_dir=%s, file_pattern=%s",
                self._base_dir,
                file_pattern,
            )

    async def get(
        self, key: str, as_bytes: bool | None = False, encoding: str | None = None
    ) -> Any:
        """Get a value from the blob."""
        try:
            key = self._keyname(key)
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            blob_client = container_client.get_blob_client(key)
            blob_data = blob_client.download_blob().readall()
            if not as_bytes:
                coding = encoding or self._encoding
                blob_data = blob_data.decode(coding)
        except Exception:  # noqa: BLE001
            logger.warning("Error getting key %s", key)
            return None
        else:
            return blob_data

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set a value in the blob."""
        try:
            key = self._keyname(key)
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            blob_client = container_client.get_blob_client(key)
            if isinstance(value, bytes):
                blob_client.upload_blob(value, overwrite=True)
            else:
                coding = encoding or self._encoding
                blob_client.upload_blob(value.encode(coding), overwrite=True)
        except Exception:
            logger.exception("Error setting key %s: %s", key)

    async def has(self, key: str) -> bool:
        """Check if a key exists in the blob."""
        key = self._keyname(key)
        container_client = self._blob_service_client.get_container_client(
            self._container_name
        )
        blob_client = container_client.get_blob_client(key)
        return blob_client.exists()

    async def delete(self, key: str) -> None:
        """Delete a key from the blob."""
        key = self._keyname(key)
        container_client = self._blob_service_client.get_container_client(
            self._container_name
        )
        blob_client = container_client.get_blob_client(key)
        blob_client.delete_blob()

    async def clear(self) -> None:
        """Clear the cache."""

    def child(self, name: str | None) -> "Storage":
        """Create a child storage instance."""
        if name is None:
            return self
        path = str(Path(self._base_dir) / name) if self._base_dir else name
        return AzureBlobStorage(
            connection_string=self._connection_string,
            container_name=self._container_name,
            encoding=self._encoding,
            base_dir=path,
            account_url=self._account_url,
        )

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        msg = "Blob storage does yet not support listing keys."
        raise NotImplementedError(msg)

    def _keyname(self, key: str) -> str:
        """Get the key name."""
        return str(Path(self._base_dir) / key) if self._base_dir else key

    async def get_creation_date(self, key: str) -> str:
        """Get creation date for the blob."""
        try:
            key = self._keyname(key)
            container_client = self._blob_service_client.get_container_client(
                self._container_name
            )
            blob_client = container_client.get_blob_client(key)
            timestamp = blob_client.download_blob().properties.creation_time
            return get_timestamp_formatted_with_local_tz(timestamp)
        except Exception:  # noqa: BLE001
            logger.warning("Error getting key %s", key)
            return ""


def _validate_blob_container_name(container_name: str) -> None:
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
    # Match alphanumeric or single hyphen not at the start or end, repeated 3-63 times.
    if not re.match(r"^(?:[0-9a-z]|(?<!^)-(?!$)){3,63}$", container_name):
        msg = f"Container name must be between 3 and 63 characters long and contain only lowercase letters, numbers, or hyphens. Name provided was {container_name}."
        raise ValueError(msg)
