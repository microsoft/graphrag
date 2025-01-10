# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Errors for the default configuration."""


class ApiKeyMissingError(ValueError):
    """LLM Key missing error."""

    def __init__(self, llm_type: str, azure_auth_type: str | None = None) -> None:
        """Init method definition."""
        msg = f"API Key is required for {llm_type}"
        if azure_auth_type:
            msg += f" when using {azure_auth_type} authentication"
        msg += ". Please set the API_KEY."
        super().__init__(msg)


class AzureApiBaseMissingError(ValueError):
    """Azure API Base missing error."""

    def __init__(self, llm_type: str) -> None:
        """Init method definition."""
        msg = f"API Base is required for {llm_type}. Please set the api_base."
        super().__init__(msg)


class AzureApiVersionMissingError(ValueError):
    """Azure API version missing error."""

    def __init__(self, llm_type: str) -> None:
        """Init method definition."""
        msg = f"API Version is required for {llm_type}. Please set the api_version."
        super().__init__(msg)


class AzureDeploymentNameMissingError(ValueError):
    """Azure Deployment Name missing error."""

    def __init__(self, llm_type: str) -> None:
        """Init method definition."""
        msg = f"Deployment name is required for {llm_type}. Please set the deployment_name."
        super().__init__(msg)


class LanguageModelConfigMissingError(ValueError):
    """Missing model configuration error."""

    def __init__(self, key: str = "") -> None:
        """Init method definition."""
        msg = f'A {key} model configuration is required. Please set models["{key}"] in settings.yaml or rerun graphrag init'
        super().__init__(msg)
