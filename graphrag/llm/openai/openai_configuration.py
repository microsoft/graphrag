# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""OpenAI Configuration class definition."""

import json
from collections.abc import Hashable
from typing import Any, cast

from graphrag.llm.types import LLMConfig


def _non_blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return None if stripped == "" else value


class OpenAIConfiguration(Hashable, LLMConfig):
    """OpenAI Configuration class definition."""

    # Core Configuration
    _api_key: str
    _model: str

    _api_base: str | None
    _api_version: str | None
    _audience: str | None
    _deployment_name: str | None
    _organization: str | None
    _proxy: str | None

    # Operation Configuration
    _n: int | None
    _temperature: float | None
    _frequency_penalty: float | None
    _presence_penalty: float | None
    _top_p: float | None
    _max_tokens: int | None
    _response_format: str | None
    _logit_bias: dict[str, float] | None
    _stop: list[str] | None

    # Retry Logic
    _max_retries: int | None
    _max_retry_wait: float | None
    _request_timeout: float | None

    # The raw configuration object
    _raw_config: dict

    # Feature Flags
    _model_supports_json: bool | None

    # Custom Configuration
    _tokens_per_minute: int | None
    _requests_per_minute: int | None
    _concurrent_requests: int | None
    _encoding_model: str | None
    _sleep_on_rate_limit_recommendation: bool | None

    def __init__(
        self,
        config: dict,
    ):
        """Init method definition."""

        def lookup_required(key: str) -> str:
            return cast(str, config.get(key))

        def lookup_str(key: str) -> str | None:
            return cast(str | None, config.get(key))

        def lookup_int(key: str) -> int | None:
            result = config.get(key)
            if result is None:
                return None
            return int(cast(int, result))

        def lookup_float(key: str) -> float | None:
            result = config.get(key)
            if result is None:
                return None
            return float(cast(float, result))

        def lookup_dict(key: str) -> dict | None:
            return cast(dict | None, config.get(key))

        def lookup_list(key: str) -> list | None:
            return cast(list | None, config.get(key))

        def lookup_bool(key: str) -> bool | None:
            value = config.get(key)
            if isinstance(value, str):
                return value.upper() == "TRUE"
            if isinstance(value, int):
                return value > 0
            return cast(bool | None, config.get(key))

        self._api_key = lookup_required("api_key")
        self._model = lookup_required("model")
        self._deployment_name = lookup_str("deployment_name")
        self._api_base = lookup_str("api_base")
        self._api_version = lookup_str("api_version")
        self._audience = lookup_str("audience")
        self._organization = lookup_str("organization")
        self._proxy = lookup_str("proxy")
        self._n = lookup_int("n")
        self._temperature = lookup_float("temperature")
        self._frequency_penalty = lookup_float("frequency_penalty")
        self._presence_penalty = lookup_float("presence_penalty")
        self._top_p = lookup_float("top_p")
        self._max_tokens = lookup_int("max_tokens")
        self._response_format = lookup_str("response_format")
        self._logit_bias = lookup_dict("logit_bias")
        self._stop = lookup_list("stop")
        self._max_retries = lookup_int("max_retries")
        self._request_timeout = lookup_float("request_timeout")
        self._model_supports_json = lookup_bool("model_supports_json")
        self._tokens_per_minute = lookup_int("tokens_per_minute")
        self._requests_per_minute = lookup_int("requests_per_minute")
        self._concurrent_requests = lookup_int("concurrent_requests")
        self._encoding_model = lookup_str("encoding_model")
        self._max_retry_wait = lookup_float("max_retry_wait")
        self._sleep_on_rate_limit_recommendation = lookup_bool(
            "sleep_on_rate_limit_recommendation"
        )
        self._raw_config = config

    @property
    def api_key(self) -> str:
        """API key property definition."""
        return self._api_key

    @property
    def model(self) -> str:
        """Model property definition."""
        return self._model

    @property
    def deployment_name(self) -> str | None:
        """Deployment name property definition."""
        return _non_blank(self._deployment_name)

    @property
    def api_base(self) -> str | None:
        """API base property definition."""
        result = _non_blank(self._api_base)
        # Remove trailing slash
        return result[:-1] if result and result.endswith("/") else result

    @property
    def api_version(self) -> str | None:
        """API version property definition."""
        return _non_blank(self._api_version)

    @property
    def audience(self) -> str | None:
        """API version property definition."""
        return _non_blank(self._audience)

    @property
    def organization(self) -> str | None:
        """Organization property definition."""
        return _non_blank(self._organization)

    @property
    def proxy(self) -> str | None:
        """Proxy property definition."""
        return _non_blank(self._proxy)

    @property
    def n(self) -> int | None:
        """N property definition."""
        return self._n

    @property
    def temperature(self) -> float | None:
        """Temperature property definition."""
        return self._temperature

    @property
    def frequency_penalty(self) -> float | None:
        """Frequency penalty property definition."""
        return self._frequency_penalty

    @property
    def presence_penalty(self) -> float | None:
        """Presence penalty property definition."""
        return self._presence_penalty

    @property
    def top_p(self) -> float | None:
        """Top p property definition."""
        return self._top_p

    @property
    def max_tokens(self) -> int | None:
        """Max tokens property definition."""
        return self._max_tokens

    @property
    def response_format(self) -> str | None:
        """Response format property definition."""
        return _non_blank(self._response_format)

    @property
    def logit_bias(self) -> dict[str, float] | None:
        """Logit bias property definition."""
        return self._logit_bias

    @property
    def stop(self) -> list[str] | None:
        """Stop property definition."""
        return self._stop

    @property
    def max_retries(self) -> int | None:
        """Max retries property definition."""
        return self._max_retries

    @property
    def max_retry_wait(self) -> float | None:
        """Max retry wait property definition."""
        return self._max_retry_wait

    @property
    def request_timeout(self) -> float | None:
        """Request timeout property definition."""
        return self._request_timeout

    @property
    def model_supports_json(self) -> bool | None:
        """Model supports json property definition."""
        return self._model_supports_json

    @property
    def tokens_per_minute(self) -> int | None:
        """Tokens per minute property definition."""
        return self._tokens_per_minute

    @property
    def requests_per_minute(self) -> int | None:
        """Requests per minute property definition."""
        return self._requests_per_minute

    @property
    def concurrent_requests(self) -> int | None:
        """Concurrent requests property definition."""
        return self._concurrent_requests

    @property
    def encoding_model(self) -> str | None:
        """Encoding model property definition."""
        return _non_blank(self._encoding_model)

    @property
    def sleep_on_rate_limit_recommendation(self) -> bool | None:
        """Whether to sleep for <n> seconds when recommended by 429 errors (azure-specific)."""
        return self._sleep_on_rate_limit_recommendation

    @property
    def raw_config(self) -> dict:
        """Raw config method definition."""
        return self._raw_config

    def lookup(self, name: str, default_value: Any = None) -> Any:
        """Lookup method definition."""
        return self._raw_config.get(name, default_value)

    def __str__(self) -> str:
        """Str method definition."""
        return json.dumps(self.raw_config, indent=4)

    def __repr__(self) -> str:
        """Repr method definition."""
        return f"OpenAIConfiguration({self._raw_config})"

    def __eq__(self, other: object) -> bool:
        """Eq method definition."""
        if not isinstance(other, OpenAIConfiguration):
            return False
        return self._raw_config == other._raw_config

    def __hash__(self) -> int:
        """Hash method definition."""
        return hash(tuple(sorted(self._raw_config.items())))
