# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Ollama Configuration class definition."""
import json
from collections.abc import Hashable
from typing import cast, Any

from graphrag.llm import LLMConfig
from graphrag.llm.utils import non_blank, non_none_value_key


class OllamaConfiguration(Hashable, LLMConfig):
    """OpenAI Configuration class definition."""

    # Core Configuration
    _api_key: str
    _model: str

    _api_base: str | None
    _api_version: str | None
    _organization: str | None

    # Operation Configuration
    _n: int | None
    _temperature: float | None
    _top_p: float | None
    _format: str | None
    _stop: str | None
    _mirostat: int | None
    _mirostat_eta: float | None
    _mirostat_tau: float | None
    _num_ctx: int | None
    _repeat_last_n: int | None
    _repeat_penalty: float | None
    _frequency_penalty: float | None
    _seed: int | None
    _tfs_z: float | None
    _num_predict: int | None
    _top_k: int | None
    _min_p: float | None
    _options: dict | None
    _suffix: str | None
    _system: str | None
    _template: str | None
    _raw: bool | None
    _keep_alive: int | None
    _stream: bool | None

    # embedding
    _truncate: bool | None

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
        self._api_base = lookup_str("api_base")
        self._api_version = lookup_str("api_version")
        self._organization = lookup_str("organization")
        self._n = lookup_int("n")
        self._temperature = lookup_float("temperature")
        self._top_p = lookup_float("top_p")
        self._stop = lookup_str("stop")
        self._mirostat = lookup_int("mirostat")
        self._mirostat_eta = lookup_float("mirostat_eta")
        self._mirostat_tau = lookup_float("mirostat_tau")
        self._num_ctx = lookup_int("max_tokens")
        self._repeat_last_n = lookup_int("repeat_last_n")
        self._repeat_penalty = lookup_float("repeat_penalty")
        self._frequency_penalty = lookup_float("frequency_penalty")
        self._seed = lookup_int("seed")
        self._tfs_z = lookup_float("tfs_z")
        self._num_predict = lookup_int("num_predict")
        self._top_k = lookup_int("top_k")
        self._min_p = lookup_float("min_p")
        self._suffix = lookup_str("suffix")
        self._system = lookup_str("system")
        self._template = lookup_str("template")
        self._raw = lookup_bool("raw")
        self._keep_alive = lookup_int("keep_alive")
        self._stream = lookup_bool("stream")
        self._format = lookup_str("response_format")
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
        self._options = {
            "n": self._n,
            "temperature": self._temperature,
            "top_p": self._top_p,
            "format": self._format,
            "stop": self._stop,
            "mirostat": self._mirostat,
            "mirostat_eta": self._mirostat_eta,
            "mirostat_tau": self._mirostat_tau,
            "num_ctx": self._num_ctx,
            "repeat_last_n": self._repeat_last_n,
            "repeat_penalty": self._repeat_penalty,
            "frequency_penalty": self._frequency_penalty,
            "seed": self._seed,
            "tfs_z": self._tfs_z,
            "num_predict": self._num_predict,
            "top_k": self._top_k,
            "min_p": self._min_p,
            "suffix": self._suffix,
            "system": self._system,
            "template": self._template,
            "raw": self._raw,
            "keep_alive": self._keep_alive,
        }
        self._truncate = lookup_bool("truncate")

    @property
    def api_key(self) -> str:
        """API key property definition."""
        return self._api_key

    @property
    def model(self) -> str:
        """Model property definition."""
        return self._model

    @property
    def api_base(self) -> str | None:
        """API base property definition."""
        result = non_blank(self._api_base)
        # Remove trailing slash
        return result[:-1] if result and result.endswith("/") else result

    @property
    def api_version(self) -> str | None:
        """API version property definition."""
        return non_blank(self._api_version)

    @property
    def organization(self) -> str | None:
        """Organization property definition."""
        return non_blank(self._organization)

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
    def top_p(self) -> float | None:
        """Top p property definition."""
        return self._top_p

    @property
    def stop(self) -> str | None:
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
        return non_blank(self._encoding_model)

    @property
    def sleep_on_rate_limit_recommendation(self) -> bool | None:
        """Whether to sleep for <n> seconds when recommended by 429 errors (azure-specific)."""
        return self._sleep_on_rate_limit_recommendation

    @property
    def raw_config(self) -> dict:
        """Raw config method definition."""
        return self._raw_config

    @property
    def format(self) -> str | None:
        """The format to return a response in. Currently the only accepted value is json"""
        return self._format

    @property
    def mirostat(self):
        """
        Enable Mirostat sampling for controlling perplexity.
        (default: 0, 0 = disabled, 1 = Mirostat, 2 = Mirostat 2.0)
        """
        return self._mirostat

    @property
    def mirostat_eta(self):
        """
        Influences how quickly the algorithm responds to feedback from the generated text.
        A lower learning rate will result in slower adjustments,
        while a higher learning rate will make the algorithm more responsive.
        (Default: 0.1)
        """
        return self._mirostat_eta

    @property
    def mirostat_tau(self):
        """
        Controls the balance between coherence and diversity of the output.
        A lower value will result in more focused and coherent text.
        (Default: 5.0)
        """
        return self._mirostat_tau

    @property
    def num_ctx(self):
        """Sets the size of the context window used to generate the next token. (Default: 2048)"""
        return self._num_ctx

    @property
    def repeat_last_n(self):
        """
        Sets how far back for the model to look back to prevent repetition.
        (Default: 64, 0 = disabled, -1 = num_ctx)
        """
        return self._repeat_last_n

    @property
    def repeat_penalty(self):
        """
        Sets how strongly to penalize repetitions.
        A higher value (e.g., 1.5) will penalize repetitions more strongly,
        while a lower value (e.g., 0.9) will be more lenient. (Default: 1.1)
        """
        return self._repeat_penalty

    @property
    def seed(self):
        """
        Sets the random number seed to use for generation.
        Setting this to a specific number will make the model generate the same text for the same prompt.
        (Default: 0)
        """
        return self._seed

    @property
    def tfs_z(self):
        """
        Tail free sampling is used to reduce the impact of less probable tokens from the output.
        A higher value (e.g., 2.0) will reduce the impact more, while a value of 1.0 disables this setting.
        (default: 1)
        """
        return self._tfs_z

    @property
    def num_predict(self):
        """
        Maximum number of tokens to predict when generating text.
        (Default: 128, -1 = infinite generation, -2 = fill context)
        """
        return self._num_predict

    @property
    def top_k(self):
        """
        Reduces the probability of generating nonsense.
        A higher value (e.g. 100) will give more diverse answers,
        while a lower value (e.g. 10) will be more conservative.
        (Default: 40)
        """
        return self._top_k

    @property
    def min_p(self):
        """Alternative to the top_p, and aims to ensure a balance of quality and variety.
        The parameter p represents the minimum probability for a token to be considered,
        relative to the probability of the most likely token.
        For example, with p=0.05 and the most likely token having a probability of 0.9,
        logits with a value less than 0.045 are filtered out.
        (Default: 0.0)
        """
        return self._min_p

    @property
    def suffix(self):
        """See https://github.com/ollama/ollama/blob/main/docs/modelfile.md#template"""
        return self._suffix

    @property
    def system(self):
        """The SYSTEM instruction specifies the system message to be used in the template, if applicable."""
        return self._system

    @property
    def template(self):
        """See https://github.com/ollama/ollama/blob/main/docs/modelfile.md#template"""
        return self._template

    @property
    def raw(self):
        """
        If true no formatting will be applied to the prompt.
        You may choose to use the raw parameter if you are specifying a full templated prompt in your request to the API
        """
        return self._raw

    @property
    def keep_alive(self):
        """
        Controls how long the model will stay loaded into memory following the request.
        (default: 5m)
        """
        return self._keep_alive

    @property
    def stream(self):
        """
        If false the response will be returned as a single response object, rather than a stream of objects.
        (default: True)
        """
        return self._stream

    @property
    def options(self) -> dict:
        """Additional model parameters listed in the documentation for the Modelfile such as temperature"""
        return non_none_value_key(
            {
                "n": self.n,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "format": self.format,
                "stop": self.stop,
                "mirostat": self.mirostat,
                "mirostat_eta": self.mirostat_eta,
                "mirostat_tau": self.mirostat_tau,
                "num_ctx": self.num_ctx,
                "repeat_last_n": self.repeat_last_n,
                "repeat_penalty": self.repeat_penalty,
                "frequency_penalty": self.frequency_penalty,
                "seed": self.seed,
                "tfs_z": self.tfs_z,
                "num_predict": self.num_predict,
                "top_k": self.top_k,
                "min_p": self.min_p,
                "suffix": self.suffix,
                "system": self.system,
                "template": self.template,
                "raw": self.raw,
                "keep_alive": self.keep_alive,
            }
        )

    @property
    def truncate(self):
        """
        truncates the end of each input to fit within context length.
        Returns error if false and context length is exceeded.
        Defaults to true
        """
        return self._truncate

    def lookup(self, name: str, default_value: Any = None) -> Any:
        """Lookup method definition."""
        return self._raw_config.get(name, default_value)

    def get_completion_cache_args(self):
        """Get the cache arguments for a completion(generate) LLM."""
        return non_none_value_key(
            {
                "model": self.model,
                "suffix": self.suffix,
                "format": self.format,
                "system": self.system,
                "template": self.template,
                # "context": self.context,
                "options": self.options,
                "stream": self.stream,
                "raw": self.raw,
                "keep_alive": self.keep_alive,
            }
        )

    def get_chat_cache_args(self) -> dict:
        """Get the cache arguments for a chat LLM."""
        return non_none_value_key(
            {
                "model": self.model,
                "format": self.format,
                "options": self.options,
                "stream": self.stream,
                "keep_alive": self.keep_alive,
            }
        )

    def get_embed_cache_args(self) -> dict:
        """Get cache arguments for a embedding LLM."""
        return non_none_value_key(
            {
                "model": self.model,
                "options": self.options,
                "keep_alive": self.keep_alive,
                "truncate": self.truncate,
            }
        )

    def __str__(self) -> str:
        """Str method definition."""
        return json.dumps(self.raw_config, indent=4)

    def __repr__(self) -> str:
        """Repr method definition."""
        return f"OpenAIConfiguration({self._raw_config})"

    def __eq__(self, other: object) -> bool:
        """Eq method definition."""
        if not isinstance(other, OllamaConfiguration):
            return False
        return self._raw_config == other._raw_config

    def __hash__(self) -> int:
        """Hash method definition."""
        return hash(tuple(sorted(self._raw_config.items())))
