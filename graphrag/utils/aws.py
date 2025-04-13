# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""AWS utility functions."""

from typing import Any

import boto3
from botocore.client import BaseClient


def create_s3_client(
    endpoint_url: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    region_name: str | None = None,
    **kwargs: Any,
) -> BaseClient:
    """
    Create a boto3 S3 client with optional configuration.

    Args:
        endpoint_url (str | None, optional): The S3 endpoint URL. Defaults to None.
        aws_access_key_id (str | None, optional): AWS Access Key ID. Defaults to None.
        aws_secret_access_key (str | None, optional): AWS Secret Access Key. Defaults to None.
        region_name (str | None, optional): AWS Region Name. Defaults to None.
        **kwargs: Additional keyword arguments to pass to the boto3 client.

    Returns
    -------
        Any: The configured boto3 S3 client.
    """
    client_kwargs = {**kwargs}
    if endpoint_url and endpoint_url.strip():
        client_kwargs["endpoint_url"] = endpoint_url
    if aws_access_key_id:
        client_kwargs["aws_access_key_id"] = aws_access_key_id
    if aws_secret_access_key:
        client_kwargs["aws_secret_access_key"] = aws_secret_access_key
    if region_name:
        client_kwargs["region_name"] = region_name

    return boto3.client("s3", **client_kwargs)
