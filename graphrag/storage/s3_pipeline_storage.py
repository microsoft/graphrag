# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Module for interfacing with aws s3."""

import logging
import re
from collections.abc import Iterator
from typing import Any

from botocore.exceptions import ClientError

from graphrag.logger.base import ProgressLogger
from graphrag.logger.progress import Progress
from graphrag.storage.pipeline_storage import (
    PipelineStorage,
    get_timestamp_formatted_with_local_tz,
)
from graphrag.utils.aws import create_s3_client

log = logging.getLogger(__name__)


class S3PipelineStorage(PipelineStorage):
    """S3 storage class definition."""

    def __init__(
        self,
        bucket_name: str,
        prefix: str = "",
        encoding: str = "utf-8",
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str | None = None,
        endpoint_url: str | None = None,
    ):
        """Instantiate an instance of the `S3PipelineStorage` class.

        Args:
            bucket_name: The name of the S3 bucket.
            prefix: The prefix to use for all keys in the bucket.
            encoding: The encoding to use for text files.
            aws_access_key_id: The AWS access key ID. If not provided, boto3's credential chain will be used.
            aws_secret_access_key: The AWS secret access key. If not provided, boto3's credential chain will be used.
            region_name: The AWS region name. If not provided, boto3's default region will be used.
            endpoint_url: The endpoint URL for the S3 API. If provided, this will be used instead of the default AWS S3 endpoint.
                          This is useful for connecting to S3-compatible storage services like MinIO.
        """
        self._bucket_name = bucket_name
        self._prefix = prefix
        self._encoding = encoding
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._region_name = region_name
        self._endpoint_url = endpoint_url

        # This object will be lazily loaded
        self.__s3 = None

        log.info(
            "Initialized S3PipelineStorage with bucket: %s, prefix: %s",
            bucket_name,
            prefix,
        )

    @property
    def _s3(self):
        """Lazy load the S3 client."""
        if self.__s3 is None:
            self.__s3 = create_s3_client(
                endpoint_url=self._endpoint_url,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self._region_name,
            )

        return self.__s3

    def _get_full_key(self, key: str) -> str:
        """Get the full key with prefix.

        Args:
            key: The key to get the full key for.

        Returns
        -------
            The full key with prefix.
        """
        if not self._prefix:
            return key

        # Ensure prefix doesn't have trailing slash and key doesn't have leading slash
        prefix = self._prefix.rstrip("/")
        clean_key = key.lstrip("/")

        return f"{prefix}/{clean_key}"

    def _strip_prefix(self, key: str) -> str:
        """Strip the prefix from the key.

        Args:
            key: The key to strip the prefix from.

        Returns
        -------
            The key without the prefix.
        """
        if not self._prefix:
            return key

        prefix = self._prefix.rstrip("/") + "/"
        if key.startswith(prefix):
            return key[len(prefix) :]

        return key

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressLogger | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count: int = -1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find files in the storage using a file pattern, as well as a custom filter function.

        Args:
            file_pattern: The pattern to match files against.
            base_dir: The base directory to search in.
            progress: A progress logger to report progress to.
            file_filter: A filter to apply to the files.
            max_count: The maximum number of files to return.

        Yields
        ------
            A tuple of the file key and the match groups.
        """

        def item_filter(item: dict[str, Any]) -> bool:
            if file_filter is None:
                return True
            return all(
                re.search(value, item[key]) for key, value in file_filter.items()
            )

        search_prefix = self._prefix
        if base_dir:
            search_prefix = f"{self._prefix.rstrip('/')}/{base_dir.lstrip('/')}"

        log.info(
            "Searching S3 bucket %s with prefix %s for files matching %s",
            self._bucket_name,
            search_prefix,
            file_pattern.pattern,
        )

        # List all objects with the given prefix
        paginator = self._s3.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self._bucket_name, Prefix=search_prefix
        )

        all_objects = []
        for page in page_iterator:
            if "Contents" in page:
                all_objects.extend(page["Contents"])

        num_loaded = 0
        num_total = len(all_objects)
        num_filtered = 0

        for obj in all_objects:
            key = obj["Key"]
            match = file_pattern.search(key)
            if match:
                group = match.groupdict()
                if item_filter(group):
                    # Strip the prefix to get the relative key
                    relative_key = self._strip_prefix(key)
                    yield (relative_key, group)
                    num_loaded += 1
                    if max_count > 0 and num_loaded >= max_count:
                        break
                else:
                    num_filtered += 1
            else:
                num_filtered += 1

            if progress is not None:
                progress(
                    self._create_progress_status(num_loaded, num_filtered, num_total)
                )

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Get the value for the given key.

        Args:
            key: The key to get the value for.
            as_bytes: Whether to return the value as bytes.
            encoding: The encoding to use for text files.

        Returns
        -------
            The value for the given key.
        """
        full_key = self._get_full_key(key)

        try:
            response = self._s3.get_object(Bucket=self._bucket_name, Key=full_key)
            content = response["Body"].read()

            if as_bytes:
                return content

            return content.decode(encoding or self._encoding)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set the value for the given key.

        Args:
            key: The key to set the value for.
            value: The value to set.
            encoding: The encoding to use for text files.
        """
        full_key = self._get_full_key(key)

        if isinstance(value, bytes):
            self._s3.put_object(Bucket=self._bucket_name, Key=full_key, Body=value)
        else:
            encoded_value = value.encode(encoding or self._encoding)
            self._s3.put_object(
                Bucket=self._bucket_name, Key=full_key, Body=encoded_value
            )

    async def has(self, key: str) -> bool:
        """Return True if the given key exists in the storage.

        Args:
            key: The key to check for.

        Returns
        -------
            True if the key exists in the storage, False otherwise.
        """
        full_key = self._get_full_key(key)

        try:
            self._s3.head_object(Bucket=self._bucket_name, Key=full_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise
        else:
            return True

    async def delete(self, key: str) -> None:
        """Delete the given key from the storage.

        Args:
            key: The key to delete.
        """
        full_key = self._get_full_key(key)

        self._s3.delete_object(Bucket=self._bucket_name, Key=full_key)

    async def clear(self) -> None:
        """Clear the storage by deleting all objects with the configured prefix."""
        if not self._prefix:
            log.warning("Clearing entire S3 bucket as no prefix was specified")

        # Delete all objects with the given prefix
        objects_to_delete = {"Objects": []}

        paginator = self._s3.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self._bucket_name, Prefix=self._prefix
        )

        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    objects_to_delete["Objects"].append({"Key": obj["Key"]})

                # Delete in batches of 1000 (S3 limit)
                if len(objects_to_delete["Objects"]) >= 1000:
                    self._s3.delete_objects(
                        Bucket=self._bucket_name, Delete=objects_to_delete
                    )
                    objects_to_delete = {"Objects": []}

        # Delete any remaining objects
        if objects_to_delete["Objects"]:
            self._s3.delete_objects(Bucket=self._bucket_name, Delete=objects_to_delete)

    def child(self, name: str | None) -> "PipelineStorage":
        """Create a child storage instance.

        Args:
            name: The name of the child storage.

        Returns
        -------
            A new S3PipelineStorage instance with the child prefix.
        """
        if name is None:
            return self

        new_prefix = self._prefix
        new_prefix = f"{new_prefix.rstrip('/')}/{name}" if new_prefix else name

        # Create a new storage instance with the same parameters but a different prefix
        # Get endpoint_url from the current instance to ensure it's preserved
        return S3PipelineStorage(
            bucket_name=self._bucket_name,
            prefix=new_prefix,
            encoding=self._encoding,
            aws_access_key_id=self._aws_access_key_id,
            aws_secret_access_key=self._aws_secret_access_key,
            region_name=self._region_name,
            endpoint_url=self._endpoint_url,
        )

    def keys(self) -> list[str]:
        """List all keys in the storage.

        Returns
        -------
            A list of keys in the storage.
        """
        keys = []
        paginator = self._s3.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self._bucket_name, Prefix=self._prefix
        )

        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    # Strip the prefix to get the relative key
                    relative_key = self._strip_prefix(obj["Key"])
                    keys.append(relative_key)

        return keys

    async def get_creation_date(self, key: str) -> str:
        """Get the creation date for the given key.

        Args:
            key: The key to get the creation date for.

        Returns
        -------
            The creation date for the given key.
        """
        full_key = self._get_full_key(key)

        try:
            response = self._s3.head_object(Bucket=self._bucket_name, Key=full_key)
            last_modified = response["LastModified"]

            # S3 doesn't have a creation date, only last modified
            return get_timestamp_formatted_with_local_tz(last_modified)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                msg = f"File {key} not found in S3 bucket {self._bucket_name}"
                raise FileNotFoundError(msg) from e
            raise

    def _create_progress_status(
        self, num_loaded: int, num_filtered: int, num_total: int
    ) -> Progress:
        """Create a progress status.

        Args:
            num_loaded: The number of files loaded.
            num_filtered: The number of files filtered.
            num_total: The total number of files.

        Returns
        -------
            A Progress object.
        """
        return Progress(
            total_items=num_total,
            completed_items=num_loaded + num_filtered,
            description=f"{num_loaded} files loaded ({num_filtered} filtered)",
        )


def create_s3_storage(**kwargs: Any) -> PipelineStorage:
    """Create an S3 based storage.

    Args:
        **kwargs: Keyword arguments for the S3PipelineStorage constructor.

    Returns
    -------
        An S3PipelineStorage instance.
    """
    bucket_name = kwargs["bucket_name"]
    prefix = kwargs.get("prefix", "")
    encoding = kwargs.get("encoding", "utf-8")
    aws_access_key_id = kwargs.get("aws_access_key_id")
    aws_secret_access_key = kwargs.get("aws_secret_access_key")
    region_name = kwargs.get("region_name")
    endpoint_url = kwargs.get("endpoint_url")

    # If endpoint_url is an empty string, set it to None
    if endpoint_url == "":
        endpoint_url = None

    log.info("Creating S3 storage with bucket: %s, prefix: %s", bucket_name, prefix)

    return S3PipelineStorage(
        bucket_name=bucket_name,
        prefix=prefix,
        encoding=encoding,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
        endpoint_url=endpoint_url,
    )
