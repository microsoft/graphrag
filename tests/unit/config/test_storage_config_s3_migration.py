# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for S3 configuration migration from InputConfig to StorageConfig.

This test file documents and validates the architectural decision to move S3 connection
details from InputConfig to the generic StorageConfig class. This change was made to:

1. Centralize storage configuration in a reusable StorageConfig class
2. Avoid duplication of S3 fields across different config classes
3. Make S3 configuration consistent with other storage types
4. Enable S3 configuration reuse across input, output, cache, and other storage contexts

These tests ensure that:
- S3 fields are properly defined in StorageConfig
- S3 fields are NOT present in InputConfig (preventing regression)
- S3 configuration works correctly through the storage property
- Validation logic correctly uses the new location of S3 fields
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

import graphrag.config.defaults as defs
from graphrag.config.enums import ModelType, StorageType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.input_config import InputConfig
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.config.models.storage_config import StorageConfig

# Constants for test data
S3_FIELDS = [
    "bucket_name",
    "prefix",
    "aws_access_key_id",
    "aws_secret_access_key",
    "region_name",
    "endpoint_url",
]

STORAGE_TYPES = [
    StorageType.file,
    StorageType.blob,
    StorageType.s3,
    StorageType.cosmosdb,
]


class TestS3ConfigurationMigration:
    """Test suite for S3 configuration migration from InputConfig to StorageConfig."""

    @pytest.mark.parametrize("field", S3_FIELDS)
    def test_s3_fields_present_in_storage_config(self, field: str) -> None:
        """Test that all S3 fields are present in StorageConfig."""
        storage_config = StorageConfig()
        assert hasattr(storage_config, field), (
            f"StorageConfig should have {field} field"
        )

    @pytest.mark.parametrize("field", S3_FIELDS)
    def test_s3_fields_not_present_in_input_config(self, field: str) -> None:
        """Test that S3 fields are NOT present in InputConfig (preventing regression)."""
        input_config = InputConfig()
        assert not hasattr(input_config, field), (
            f"InputConfig should NOT have {field} field"
        )

    def test_s3_storage_config_creation(self) -> None:
        """Test creating a StorageConfig with S3 settings."""
        storage_config = StorageConfig(
            type=StorageType.s3,
            bucket_name="test-bucket",
            prefix="test-prefix",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-east-1",
            endpoint_url="http://localhost:9000",
        )

        assert storage_config.type == StorageType.s3
        assert storage_config.bucket_name == "test-bucket"
        assert storage_config.prefix == "test-prefix"
        assert storage_config.aws_access_key_id == "test-key"
        assert storage_config.aws_secret_access_key == "test-secret"
        assert storage_config.region_name == "us-east-1"
        assert storage_config.endpoint_url == "http://localhost:9000"

    def test_input_config_with_s3_storage(self) -> None:
        """Test creating InputConfig with S3 storage configuration."""
        s3_storage = StorageConfig(
            type=StorageType.s3,
            bucket_name="my-bucket",
            prefix="my-prefix",
            aws_access_key_id="my-key",
            region_name="us-west-2",
        )

        input_config = InputConfig(storage=s3_storage)

        # Verify S3 configuration is accessible through storage property
        assert input_config.storage.type == StorageType.s3
        assert input_config.storage.bucket_name == "my-bucket"
        assert input_config.storage.prefix == "my-prefix"
        assert input_config.storage.aws_access_key_id == "my-key"
        assert input_config.storage.region_name == "us-west-2"

    def _create_minimal_models(self) -> dict[str, LanguageModelConfig]:
        """Create minimal models to avoid model validation errors."""
        return {
            defs.DEFAULT_CHAT_MODEL_ID: LanguageModelConfig(
                type=ModelType.OpenAIChat, model="gpt-4", api_key="test-key"
            ),
            defs.DEFAULT_EMBEDDING_MODEL_ID: LanguageModelConfig(
                type=ModelType.OpenAIEmbedding,
                model="text-embedding-3-small",
                api_key="test-key",
            ),
        }

    @pytest.mark.parametrize(
        ("bucket_name", "should_succeed", "expected_error"),
        [
            (None, False, "S3 bucket name is required"),
            ("test-bucket", True, None),
        ],
    )
    def test_s3_validation_with_bucket_name(
        self, bucket_name: str | None, should_succeed: bool, expected_error: str | None
    ) -> None:
        """Test S3 validation based on bucket_name presence."""
        # Create S3 storage with or without bucket_name
        s3_storage = StorageConfig(type=StorageType.s3, bucket_name=bucket_name)
        input_config = InputConfig(storage=s3_storage)
        models = self._create_minimal_models()

        if should_succeed:
            # This should succeed
            config = GraphRagConfig(root_dir="/tmp", input=input_config, models=models)
            assert config.input.storage.type == StorageType.s3
            assert config.input.storage.bucket_name == bucket_name
        else:
            # This should fail validation
            with pytest.raises(ValidationError) as exc_info:
                GraphRagConfig(root_dir="/tmp", input=input_config, models=models)

            error_message = str(exc_info.value)
            assert expected_error is not None
            assert expected_error in error_message

    @pytest.mark.parametrize(
        ("field", "expected_default"),
        [
            ("bucket_name", None),
            ("prefix", ""),
            ("aws_access_key_id", None),
            ("aws_secret_access_key", None),
            ("region_name", None),
            ("endpoint_url", None),
        ],
    )
    def test_s3_defaults_in_storage_config(
        self, field: str, expected_default: str | None
    ) -> None:
        """Test that S3 fields have appropriate defaults in StorageConfig."""
        storage_config = StorageConfig()
        assert getattr(storage_config, field) == expected_default

    def test_storage_config_supports_all_s3_fields(self) -> None:
        """Test that StorageConfig supports all necessary S3 configuration fields."""
        # This test ensures we haven't missed any important S3 configuration fields
        storage_config = StorageConfig(
            type=StorageType.s3,
            bucket_name="test-bucket",
            prefix="test/prefix",
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region_name="us-east-1",
            endpoint_url="https://s3.amazonaws.com",
        )

        # Verify all fields are set correctly
        assert storage_config.type == StorageType.s3
        assert storage_config.bucket_name == "test-bucket"
        assert storage_config.prefix == "test/prefix"
        assert storage_config.aws_access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert (
            storage_config.aws_secret_access_key
            == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )
        assert storage_config.region_name == "us-east-1"
        assert storage_config.endpoint_url == "https://s3.amazonaws.com"

    def test_input_config_storage_property_exists(self) -> None:
        """Test that InputConfig has a storage property of type StorageConfig."""
        input_config = InputConfig()

        # Verify storage property exists and is of correct type
        assert hasattr(input_config, "storage")
        assert isinstance(input_config.storage, StorageConfig)

    @pytest.mark.parametrize("storage_type", STORAGE_TYPES)
    def test_storage_config_supports_all_storage_types(
        self, storage_type: StorageType
    ) -> None:
        """Test that StorageConfig supports all storage types."""
        storage_config = StorageConfig(type=storage_type)
        assert storage_config.type == storage_type

    def test_architectural_consistency(self) -> None:
        """Test that the architectural decision is consistent across the codebase.

        This test documents the architectural decision to centralize storage
        configuration in StorageConfig rather than duplicating fields across
        different config classes.
        """
        # InputConfig should delegate storage configuration to StorageConfig
        input_config = InputConfig()
        assert isinstance(input_config.storage, StorageConfig)

        # StorageConfig should have all S3 fields
        storage_config = StorageConfig()
        for field in S3_FIELDS:
            assert hasattr(storage_config, field)

        # InputConfig should NOT have S3 fields directly
        input_config = InputConfig()
        for field in S3_FIELDS:
            assert not hasattr(input_config, field)
