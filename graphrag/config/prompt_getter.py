# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Module for retrieving prompt content from various storage backends."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse

from botocore.client import BaseClient

from graphrag.utils.aws import create_s3_client

logger = logging.getLogger(__name__)


class PromptGetter(ABC):
    """Provide abstractions for getting prompt contents."""

    @abstractmethod
    def get_prompt(
        self, path: str, root_dir: str | None = None, encoding: str = "utf-8"
    ) -> str:
        """
        Retrieve the prompt content from the specified path.

        Args:
            path (str): The path to the prompt.
            root_dir (str | None): The root directory, if applicable.
            encoding (str): The encoding to use, defaults to `utf-8`.

        Returns
        -------
            str: The content of the prompt.
        """
        ...


class LocalPromptGetter(PromptGetter):
    """Class for retrieving prompts from the local filesystem."""

    def get_prompt(
        self, path: str, root_dir: str | None = None, encoding: str = "utf-8"
    ):
        """
        Retrieve the prompt content from the local filesystem.

        Args:
            path (str): The path to the prompt.
            root_dir (str | None): The root directory. Must be defined.
            encoding (str): The encoding to use, defaults to `utf-8`.

        Returns
        -------
            str: The content of the prompt.

        Raises
        ------
            ValueError: If `root_dir` is not defined.
        """
        if root_dir is None:
            msg = "`root_dir` must be defined when using `LocalPromptGetter`"
            raise ValueError(msg)

        full_path = Path(root_dir) / path
        return full_path.read_text(encoding=encoding)


class S3PromptGetter(PromptGetter):
    """Class for retrieving prompts from an S3 bucket."""

    def __init__(self, endpoint_url: str | None = None):
        """Instantiate an instance of the `S3PromptGetter` class.

        Args:
            endpoint_url: Optional endpoint URL for S3-compatible storage services like MinIO.
                          If not provided or empty, the default AWS S3 endpoint will be used.
        """
        # If endpoint_url is an empty string, set it to None to use AWS services by default
        if endpoint_url == "":
            endpoint_url = None

        self._endpoint_url = endpoint_url
        # This client will be lazily loaded
        self.__s3_client: BaseClient | None = None

    @property
    def _s3_client(self) -> BaseClient:
        """Lazy load the S3 client."""
        if self.__s3_client is None:
            self.__s3_client = create_s3_client(endpoint_url=self._endpoint_url)
        return self.__s3_client

    def get_prompt(
        self, path: str, root_dir: str | None = None, encoding: str = "utf-8"
    ):
        """
        Retrieve the prompt content from the S3 bucket.

        Args:
            path (str): The full S3 path to the prompt (e.g., 's3://bucket_name/path/to/prompt').
            root_dir (str | None): Not used. Provided here for interface consistency.
            encoding (str): The encoding to use, defaults to `utf-8`.

        Returns
        -------
            str: The content of the prompt.

        Raises
        ------
            ValueError: If `bucket_name` could not be extracted from `path`.
        """
        pased_url = urlparse(path)
        bucket_name = pased_url.netloc
        key_path = pased_url.path.lstrip("/")

        if not bucket_name:
            msg = f"Invalid S3 path. `bucket_name` could not be extracted from {path}"
            raise ValueError(msg)

        obj = self._s3_client.get_object(Bucket=bucket_name, Key=key_path)
        return obj["Body"].read().decode(encoding)


default_prompt_getter = LocalPromptGetter()


def create_prompt_getter(
    filepath: str | None, endpoint_url: str | None = None
) -> PromptGetter:
    """
    Create a `PromptGetter` instance based on the filepath.

    Args:
        filepath (str | None): The path to the prompt file. If the path starts with 's3://', it is considered an S3 path and the bucket name is extracted.
        endpoint_url (str | None): Optional endpoint URL for S3-compatible storage services like MinIO.
                                  If not provided, the default AWS S3 endpoint will be used.

    Returns
    -------
        PromptGetter: The appropriate PromptGetter instance.
    """
    if filepath and filepath.startswith("s3://"):
        logger.info("Creating the `S3PromptGetter` for %s", filepath)
        return S3PromptGetter(endpoint_url=endpoint_url)

    logger.info("Creating the `LocalPromptGetter` for %s", filepath)
    return LocalPromptGetter()


def get_prompt_content(
    prompt_path: str | None, root_dir: str | None, endpoint_url: str | None = None
) -> str | None:
    """
    Get the prompt content from a prompt path.

    Args:
        prompt_path (str | None): The path to the prompt file, or None.
        root_dir (str | None): The root directory
        endpoint_url (str | None): Optional endpoint URL for S3-compatible storage services like MinIO.
                                  If not provided, the default AWS S3 endpoint will be used.

    Returns
    -------
        The prompt content.
    """
    if not prompt_path:
        return None

    prompt_getter = create_prompt_getter(prompt_path, endpoint_url=endpoint_url)
    return prompt_getter.get_prompt(prompt_path, root_dir)
