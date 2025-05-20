# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for graphrag.utils.aws."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from botocore.client import BaseClient

from graphrag.utils.aws import create_s3_client


@pytest.mark.parametrize(
    (
        "endpoint_url",
        "aws_access_key_id",
        "aws_secret_access_key",
        "region_name",
        "extra_kwargs",
        "expected_call_kwargs",
    ),
    [
        # Test case 1: Minimal arguments (all None or default)
        (
            None,
            None,
            None,
            None,
            {},
            {},  # No optional args added
        ),
        # Test case 2: All standard arguments provided
        (
            "http://localhost:9000",
            "test_key",
            "test_secret",
            "us-west-2",
            {},
            {
                "endpoint_url": "http://localhost:9000",
                "aws_access_key_id": "test_key",
                "aws_secret_access_key": "test_secret",
                "region_name": "us-west-2",
            },
        ),
        # Test case 3: Only endpoint_url
        (
            "http://s3.amazonaws.com",
            None,
            None,
            None,
            {},
            {"endpoint_url": "http://s3.amazonaws.com"},
        ),
        # Test case 4: Only credentials
        (
            None,
            "key_only",
            "secret_only",
            None,
            {},
            {"aws_access_key_id": "key_only", "aws_secret_access_key": "secret_only"},
        ),
        # Test case 5: Only region
        (None, None, None, "eu-central-1", {}, {"region_name": "eu-central-1"}),
        # Test case 6: With extra kwargs (e.g., config)
        (
            None,
            None,
            None,
            None,
            {"config": "dummy_config_object"},
            {"config": "dummy_config_object"},  # Extra kwargs are preserved
        ),
        # Test case 7: All args + extra kwargs
        (
            "http://localhost:9001",
            "key_extra",
            "secret_extra",
            "ap-southeast-1",
            {"use_ssl": False, "verify": False},
            {
                "endpoint_url": "http://localhost:9001",
                "aws_access_key_id": "key_extra",
                "aws_secret_access_key": "secret_extra",
                "region_name": "ap-southeast-1",
                "use_ssl": False,
                "verify": False,
            },
        ),
        # Test case 8: Endpoint URL with only whitespace (should be ignored)
        (
            "   ",
            "key",
            "secret",
            "region",
            {},
            {
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "region_name": "region",
            },
        ),
        # Test case 9: Empty string for endpoint_url (should be ignored like whitespace)
        (
            "",
            "key",
            "secret",
            "region",
            {},
            {
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "region_name": "region",
            },
        ),
        # Test case 10: Empty strings for credentials and region (should NOT be included)
        (
            "http://localhost:9000",
            "",
            "",
            "",
            {},
            {
                "endpoint_url": "http://localhost:9000"
            },  # Empty strings should not be included
        ),
        # Test case 11: Complex/realistic extra kwargs
        (
            "http://s3.amazonaws.com",
            "key",
            "secret",
            "us-east-1",
            {
                "config": "complex_config",
                "connect_timeout": 30,
                "read_timeout": 60,
                "retries": {"max_attempts": 5},
            },
            {
                "endpoint_url": "http://s3.amazonaws.com",
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "region_name": "us-east-1",
                "config": "complex_config",
                "connect_timeout": 30,
                "read_timeout": 60,
                "retries": {"max_attempts": 5},
            },
        ),
        # Test case 12: Endpoint URL with special characters
        (
            "https://custom-s3.example.com/path?query=value&param=123",
            "key",
            "secret",
            "region",
            {},
            {
                "endpoint_url": "https://custom-s3.example.com/path?query=value&param=123",
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "region_name": "region",
            },
        ),
        # Test case 13: Additional kwargs (not conflicting with named args)
        (
            "http://endpoint.com",
            "key",
            "secret",
            "region",
            {"use_ssl": True, "verify": False, "config": "test_config"},
            {
                "endpoint_url": "http://endpoint.com",
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "region_name": "region",
                "use_ssl": True,
                "verify": False,
                "config": "test_config",
            },
        ),
        # Test case 14: Various AWS region formats
        (None, None, None, "us-gov-west-1", {}, {"region_name": "us-gov-west-1"}),
        # Test case 15: IPv4 endpoint URL
        (
            "http://127.0.0.1:9000",
            "key",
            "secret",
            "region",
            {},
            {
                "endpoint_url": "http://127.0.0.1:9000",
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "region_name": "region",
            },
        ),
    ],
)
@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client(
    mock_boto3_client: MagicMock,
    endpoint_url: str | None,
    aws_access_key_id: str | None,
    aws_secret_access_key: str | None,
    region_name: str | None,
    extra_kwargs: dict[str, Any],
    expected_call_kwargs: dict[str, Any],
) -> None:
    """Test the create_s3_client function with various parameter combinations."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    result = create_s3_client(
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
        **extra_kwargs,
    )

    # Assert
    # Check that boto3.client was called exactly once with the expected positional and keyword arguments
    mock_boto3_client.assert_called_once_with("s3", **expected_call_kwargs)
    # Check that the returned object is an instance of BaseClient (or a mock thereof)
    assert isinstance(result, BaseClient)
    # Check that the returned object is the one our mock created
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_boto3_error(mock_boto3_client: MagicMock) -> None:
    """Test that errors from boto3.client are properly propagated."""
    # Arrange
    mock_boto3_client.side_effect = ValueError("Invalid configuration")

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid configuration"):
        create_s3_client()


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_endpoint_url_stripping(mock_boto3_client: MagicMock) -> None:
    """Test that endpoint_url is properly stripped before checking."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    # Test with various whitespace patterns
    create_s3_client(endpoint_url="\n  \t  ")
    create_s3_client(endpoint_url="  ")
    create_s3_client(endpoint_url="\t")

    # Assert
    # Check that all calls to boto3.client were made without endpoint_url
    assert mock_boto3_client.call_count == 3
    for _call in mock_boto3_client.call_args_list:
        # Check that each call was made with just "s3" and no kwargs
        mock_boto3_client.assert_any_call("s3")


@pytest.mark.parametrize(
    "endpoint_url",
    [
        # Test with very long URL
        "https://" + "a" * 100 + ".example.com",
        # Test with URL containing various special characters
        "https://user:pass@example.com:8080/path/to/resource?query=value&param=123#fragment",
        # Test with URL containing Unicode characters
        "https://例子.测试/路径?参数=值",
    ],
)
@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_unusual_urls(
    mock_boto3_client: MagicMock, endpoint_url: str
) -> None:
    """Test create_s3_client with unusual endpoint URLs."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    result = create_s3_client(endpoint_url=endpoint_url)

    # Assert
    mock_boto3_client.assert_called_once_with("s3", endpoint_url=endpoint_url)
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_session_token(mock_boto3_client: MagicMock) -> None:
    """Test create_s3_client with AWS session token in extra kwargs."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    result = create_s3_client(
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_session_token="test_session_token",
    )

    # Assert
    mock_boto3_client.assert_called_once_with(
        "s3",
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_session_token="test_session_token",
    )
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_profile_name(mock_boto3_client: MagicMock) -> None:
    """Test create_s3_client with AWS profile name in extra kwargs."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    result = create_s3_client(profile_name="test_profile")

    # Assert
    mock_boto3_client.assert_called_once_with("s3", profile_name="test_profile")
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_boto3_config(mock_boto3_client: MagicMock) -> None:
    """Test create_s3_client with boto3 Config object."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance
    mock_config = MagicMock(name="Config")

    # Act
    result = create_s3_client(config=mock_config)

    # Assert
    mock_boto3_client.assert_called_once_with("s3", config=mock_config)
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_sts_credentials(mock_boto3_client: MagicMock) -> None:
    """Test create_s3_client with temporary STS credentials."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    result = create_s3_client(
        aws_access_key_id="ASIA...",  # STS access keys start with ASIA
        aws_secret_access_key="secret",
        aws_session_token="session_token",
        region_name="us-west-2",
    )

    # Assert
    mock_boto3_client.assert_called_once_with(
        "s3",
        aws_access_key_id="ASIA...",
        aws_secret_access_key="secret",
        aws_session_token="session_token",
        region_name="us-west-2",
    )
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_complex_config(mock_boto3_client: MagicMock) -> None:
    """Test create_s3_client with a complex configuration."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance
    mock_config = MagicMock(name="Config")

    # Act
    result = create_s3_client(
        endpoint_url="https://s3.custom-domain.com",
        aws_access_key_id="access_key",
        aws_secret_access_key="secret_key",
        region_name="eu-west-1",
        config=mock_config,
        use_ssl=True,
        verify=True,
        api_version="2006-03-01",
        use_accelerate_endpoint=True,
        addressing_style="virtual",
        s3_us_east_1_regional_endpoint="regional",
    )

    # Assert
    mock_boto3_client.assert_called_once_with(
        "s3",
        endpoint_url="https://s3.custom-domain.com",
        aws_access_key_id="access_key",
        aws_secret_access_key="secret_key",
        region_name="eu-west-1",
        config=mock_config,
        use_ssl=True,
        verify=True,
        api_version="2006-03-01",
        use_accelerate_endpoint=True,
        addressing_style="virtual",
        s3_us_east_1_regional_endpoint="regional",
    )
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_assume_role_credentials(
    mock_boto3_client: MagicMock,
) -> None:
    """Test create_s3_client with credentials from assumed role."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Simulate credentials that would be obtained from STS AssumeRole
    assumed_role_credentials = {
        "aws_access_key_id": "ASIA...",
        "aws_secret_access_key": "assumed_role_secret",
        "aws_session_token": "assumed_role_token",
    }

    # Act
    result = create_s3_client(**assumed_role_credentials)

    # Assert
    mock_boto3_client.assert_called_once_with(
        "s3",
        aws_access_key_id="ASIA...",
        aws_secret_access_key="assumed_role_secret",
        aws_session_token="assumed_role_token",
    )
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_endpoint_url_none(mock_boto3_client: MagicMock) -> None:
    """Test create_s3_client with endpoint_url explicitly set to None."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    result = create_s3_client(endpoint_url=None)

    # Assert
    # endpoint_url=None should not be included in the kwargs
    mock_boto3_client.assert_called_once_with("s3")
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_s3_specific_params(mock_boto3_client: MagicMock) -> None:
    """Test create_s3_client with S3-specific parameters."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    result = create_s3_client(
        endpoint_url="https://s3.amazonaws.com",
        # S3-specific parameters
        use_accelerate_endpoint=True,
        addressing_style="virtual",
        signature_version="s3v4",
        s3_us_east_1_regional_endpoint="regional",
    )

    # Assert
    mock_boto3_client.assert_called_once_with(
        "s3",
        endpoint_url="https://s3.amazonaws.com",
        use_accelerate_endpoint=True,
        addressing_style="virtual",
        signature_version="s3v4",
        s3_us_east_1_regional_endpoint="regional",
    )
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_credentials_and_profile(
    mock_boto3_client: MagicMock,
) -> None:
    """Test create_s3_client with both explicit credentials and profile name."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    result = create_s3_client(
        aws_access_key_id="explicit_key",
        aws_secret_access_key="explicit_secret",
        profile_name="profile_name",
    )

    # Assert
    # Both explicit credentials and profile name should be passed through
    mock_boto3_client.assert_called_once_with(
        "s3",
        aws_access_key_id="explicit_key",
        aws_secret_access_key="explicit_secret",
        profile_name="profile_name",
    )
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_empty_endpoint_url(mock_boto3_client: MagicMock) -> None:
    """Test create_s3_client with empty endpoint_url in various formats."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act & Assert
    # Test with empty string
    create_s3_client(endpoint_url="")
    mock_boto3_client.assert_called_with("s3")

    # Test with whitespace string
    mock_boto3_client.reset_mock()
    create_s3_client(endpoint_url="   ")
    mock_boto3_client.assert_called_with("s3")

    # Test with newline and tab characters
    mock_boto3_client.reset_mock()
    create_s3_client(endpoint_url="\n\t")
    mock_boto3_client.assert_called_with("s3")


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_connection_parameters(
    mock_boto3_client: MagicMock,
) -> None:
    """Test create_s3_client with connection-related parameters."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    result = create_s3_client(
        endpoint_url="https://s3.amazonaws.com",
        # Connection parameters
        connect_timeout=10,
        read_timeout=20,
        max_pool_connections=10,
        socket_timeout=30,
        proxies={"http": "http://proxy.example.com"},
    )

    # Assert
    mock_boto3_client.assert_called_once_with(
        "s3",
        endpoint_url="https://s3.amazonaws.com",
        connect_timeout=10,
        read_timeout=20,
        max_pool_connections=10,
        socket_timeout=30,
        proxies={"http": "http://proxy.example.com"},
    )
    assert result == mock_client_instance


@patch("graphrag.utils.aws.boto3.client")
def test_create_s3_client_with_retry_parameters(mock_boto3_client: MagicMock) -> None:
    """Test create_s3_client with retry-related parameters."""
    # Arrange
    mock_client_instance = MagicMock(spec=BaseClient)
    mock_boto3_client.return_value = mock_client_instance

    # Act
    result = create_s3_client(
        endpoint_url="https://s3.amazonaws.com",
        # Retry parameters
        retries={"max_attempts": 5, "mode": "standard"},
    )

    # Assert
    mock_boto3_client.assert_called_once_with(
        "s3",
        endpoint_url="https://s3.amazonaws.com",
        retries={"max_attempts": 5, "mode": "standard"},
    )
    assert result == mock_client_instance
