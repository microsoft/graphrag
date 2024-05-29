# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM Parameters model."""

from typing_extensions import NotRequired, TypedDict

from graphrag.config.enums import LLMType


class LLMParametersInput(TypedDict):
    """LLM Parameters model."""

    api_key: NotRequired[str | None]
    type: NotRequired[LLMType | str | None]
    model: NotRequired[str | None]
    max_tokens: NotRequired[int | str | None]
    request_timeout: NotRequired[float | str | None]
    api_base: NotRequired[str | None]
    api_version: NotRequired[str | None]
    organization: NotRequired[str | None]
    proxy: NotRequired[str | None]
    cognitive_services_endpoint: NotRequired[str | None]
    deployment_name: NotRequired[str | None]
    model_supports_json: NotRequired[bool | str | None]
    tokens_per_minute: NotRequired[int | str | None]
    requests_per_minute: NotRequired[int | str | None]
    max_retries: NotRequired[int | str | None]
    max_retry_wait: NotRequired[float | str | None]
    sleep_on_rate_limit_recommendation: NotRequired[bool | str | None]
    concurrent_requests: NotRequired[int | str | None]
