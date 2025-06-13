# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Integration tests for S3 storage factory with the new StorageConfig architecture.

This test file validates that the storage factory correctly creates S3 storage
instances using the new StorageConfig architecture where S3 fields are centralized
in StorageConfig rather than being duplicated across different config classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import pytest

from graphrag.config.enums import StorageType
from graphrag.config.models.storage_config import StorageConfig
from graphrag.utils.api import create_storage_from_config

if TYPE_CHECKING:
    from graphrag.storage.pipeline_storage import PipelineStorage
    from graphrag.storage.s3_pipeline_storage import S3PipelineStorage


class TestStorageFactoryS3Integration:
    """Test suite for S3 storage factory integration with StorageConfig."""

    def _trigger_s3_client_loading(self, storage: PipelineStorage) -> None:
        """Trigger lazy loading of the S3 client."""
        # Access _s3 property using getattr to avoid type checking issues
        _ = getattr(storage, "_s3", None)

    @pytest.mark.parametrize(
        ("config_data", "expected_bucket", "expected_calls"),
        [
            (
                {
                    "type": StorageType.s3,
                    "bucket_name": "test-bucket",
                    "prefix": "test-prefix",
                    "aws_access_key_id": "test-key",
                    "aws_secret_access_key": "test-secret",
                    "region_name": "us-east-1",
                    "endpoint_url": "http://localhost:9000",
                },
                "test-bucket",
                {
                    "endpoint_url": "http://localhost:9000",
                    "aws_access_key_id": "test-key",
                    "aws_secret_access_key": "test-secret",
                    "region_name": "us-east-1",
                },
            ),
            (
                {"type": StorageType.s3, "bucket_name": "minimal-bucket"},
                "minimal-bucket",
                {},  # No specific parameters expected for minimal config
            ),
        ],
    )
    @patch("graphrag.utils.aws.boto3.client")
    def test_create_s3_storage_from_storage_config(
        self,
        mock_boto3_client: MagicMock,
        config_data: dict[str, Any],
        expected_bucket: str,
        expected_calls: dict[str, str],
    ) -> None:
        """Test creating S3 storage from StorageConfig using the storage factory."""
        # Create a StorageConfig with S3 settings
        storage_config = StorageConfig(**config_data)

        # Create storage using the factory
        storage: S3PipelineStorage = cast(
            "S3PipelineStorage", create_storage_from_config(storage_config)
        )

        # Verify the storage was created correctly
        assert storage is not None
        assert hasattr(storage, "_bucket_name")
        assert storage._bucket_name == expected_bucket  # noqa: SLF001

        # Trigger lazy loading of the S3 client
        self._trigger_s3_client_loading(storage)

        # Verify boto3 client was called
        mock_boto3_client.assert_called_once()

        # Check specific parameters if provided
        if expected_calls:
            call_kwargs = mock_boto3_client.call_args.kwargs
            for key, value in expected_calls.items():
                assert call_kwargs[key] == value

    @pytest.mark.parametrize(
        ("field", "expected_value"),
        [
            ("type", "s3"),
            ("bucket_name", "test-bucket"),
            ("prefix", "test-prefix"),
            ("aws_access_key_id", "test-key"),
            ("aws_secret_access_key", "test-secret"),
            ("region_name", "us-east-1"),
            ("endpoint_url", "http://localhost:9000"),
        ],
    )
    def test_storage_config_model_dump_includes_s3_fields(
        self, field: str, expected_value: str
    ) -> None:
        """Test that StorageConfig.model_dump() includes all S3 fields for the factory."""
        storage_config = StorageConfig(
            type=StorageType.s3,
            bucket_name="test-bucket",
            prefix="test-prefix",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-east-1",
            endpoint_url="http://localhost:9000",
        )

        # Get the model dump (this is what gets passed to the storage factory)
        config_dict = storage_config.model_dump()

        # Verify the specific field is included with correct value
        assert config_dict[field] == expected_value

    @patch("graphrag.utils.aws.boto3.client")
    def test_storage_config_with_base_dir_creates_child_storage(
        self, mock_boto3_client: MagicMock
    ) -> None:
        """Test that StorageConfig with base_dir creates child storage correctly."""
        storage_config = StorageConfig(
            type=StorageType.s3, bucket_name="test-bucket", base_dir="input"
        )

        # The storage factory should create a child storage when base_dir is provided
        storage: S3PipelineStorage = cast(
            "S3PipelineStorage", create_storage_from_config(storage_config)
        )

        # Verify it's a child storage with the correct prefix
        assert hasattr(storage, "_prefix")
        assert "input" in storage._prefix  # noqa: SLF001

    @pytest.mark.parametrize(
        ("field", "expected_default"),
        [
            ("prefix", ""),
            ("aws_access_key_id", None),
            ("aws_secret_access_key", None),
            ("region_name", None),
            ("endpoint_url", None),
        ],
    )
    @patch("graphrag.utils.aws.boto3.client")
    def test_storage_config_defaults_work_with_factory(
        self, mock_boto3_client: MagicMock, field: str, expected_default: str | None
    ) -> None:
        """Test that StorageConfig defaults work correctly with the storage factory."""
        # Create StorageConfig with defaults
        storage_config = StorageConfig(type=StorageType.s3, bucket_name="test-bucket")

        # Verify defaults are set correctly
        assert getattr(storage_config, field) == expected_default

        # Verify the factory can handle these defaults
        storage = create_storage_from_config(storage_config)
        assert storage is not None
