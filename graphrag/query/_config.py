# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import os
import pathlib
import typing
import warnings

import pydantic
import pydantic_settings

from . import errors as _errors

__all__ = [
    'ChatLLMConfig',
    'EmbeddingConfig',
    'LoggingConfig',
    'ContextConfig',
    'LocalSearchConfig',
    'GlobalSearchConfig',
    'GraphRAGConfig',
]


class ChatLLMConfig(pydantic.BaseModel):
    model: typing.Annotated[str, pydantic.Field(..., env="MODEL")]
    api_key: typing.Annotated[str, pydantic.Field(..., env="API_KEY", repr=False)]

    # Optional fields
    base_url: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(
            ..., env="BASE_URL", pattern=r"https?://([a-zA-Z0-9\-.]+\.[a-zA-Z]{2,})(:[0-9]{1,5})?(/\s*)?"
        )
    ] = None
    organization: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="ORGANIZATION")
    ] = None
    timeout: typing.Annotated[
        typing.Optional[float],
        pydantic.Field(..., env="TIMEOUT", gt=0, lt=60)
    ] = None
    max_retries: typing.Annotated[
        typing.Optional[int],
        pydantic.Field(..., env="MAX_RETRIES", ge=0, le=10)
    ] = None
    kwargs: typing.Annotated[
        typing.Optional[typing.Dict[str, typing.Any]],
        pydantic.Field(..., env="KWARGS")
    ] = None

    @pydantic.field_serializer('api_key')
    def __serialize_masked(self, _: str) -> None: ...


class EmbeddingConfig(pydantic.BaseModel):
    model: typing.Annotated[str, pydantic.Field(..., env="MODEL")]
    api_key: typing.Annotated[str, pydantic.Field(..., env="API_KEY", repr=False)]

    # Optional fields
    base_url: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(
            ..., env="BASE_URL", pattern=r"https?://([a-zA-Z0-9\-.]+\.[a-zA-Z]{2,})(:[0-9]{1,5})?(/\s*)?"
        )
    ] = None
    organization: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="ORGANIZATION")
    ] = None
    timeout: typing.Annotated[
        typing.Optional[float],
        pydantic.Field(..., env="TIMEOUT", gt=0, lt=60)
    ] = None
    max_retries: typing.Annotated[
        typing.Optional[int],
        pydantic.Field(..., env="MAX_RETRIES", ge=0, le=10)
    ] = None
    max_tokens: typing.Annotated[
        typing.Optional[int],
        pydantic.Field(..., env="MAX_TOKENS", ge=1)
    ] = None
    token_encoder: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="TOKEN_ENCODER", pattern=r"^[a-zA-Z0-9_]+$")
    ] = None
    kwargs: typing.Annotated[
        typing.Optional[typing.Dict[str, typing.Any]],
        pydantic.Field(..., env="KWARGS")
    ] = None

    @pydantic.field_serializer('api_key')
    def __serialize_masked(self, _: str) -> None: ...


class LoggingConfig(pydantic.BaseModel):
    enabled: typing.Annotated[bool, pydantic.Field(..., env="ENABLED")]

    # Optional fields
    level: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="LEVEL", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    ] = None
    format: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="FORMAT", min_length=1)
    ] = None
    out_file: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="OUT_FILE", min_length=1)
    ] = None
    err_file: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="ERR_FILE", min_length=1)
    ] = None
    rotation: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="ROTATION", pattern=r"^\d+ (second|minute|hour|day|week|month|year)s?$")
    ] = None
    retention: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="RETENTION", pattern=r"^\d+ (second|minute|hour|day|week|month|year)s?$")
    ] = None
    serialize: typing.Annotated[
        typing.Optional[bool],
        pydantic.Field(..., env="SERIALIZE")
    ] = None
    kwargs: typing.Annotated[
        typing.Optional[typing.Dict[str, typing.Any]],
        pydantic.Field(..., env="KWARGS")
    ] = None


class ContextConfig(pydantic.BaseModel):
    directory: typing.Annotated[str, pydantic.Field(..., env="DIRECTORY", min_length=1)]

    # Optional fields
    kwargs: typing.Annotated[
        typing.Optional[typing.Dict[str, typing.Any]],
        pydantic.Field(..., env="KWARGS")
    ] = None


class LocalSearchConfig(pydantic.BaseModel):
    sys_prompt: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="SYS_PROMPT", min_length=1, repr=False)
    ] = None
    community_level: typing.Annotated[
        typing.Optional[int],
        pydantic.Field(..., env="COMMUNITY_LEVEL", ge=0)
    ] = None
    store_coll_name: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="STORE_COLL_NAME", min_length=1)
    ] = None
    store_uri: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="STORE_URI", min_length=1)
    ] = None
    encoding_model: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="ENCODING_MODEL", min_length=1)
    ] = None
    kwargs: typing.Annotated[
        typing.Optional[typing.Dict[str, typing.Any]],
        pydantic.Field(..., env="KWARGS")
    ] = None

    @pydantic.field_serializer('sys_prompt')
    def __serialize_prompt(self, prompt: typing.Optional[str]) -> typing.Optional[str]:
        return prompt[:50] + '...' if prompt and len(prompt) > 50 else prompt

    @pydantic.field_serializer('store_uri')
    def __serialize_masked(self, _: str) -> None: ...


class GlobalSearchConfig(pydantic.BaseModel):
    map_sys_prompt: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="MAP_SYS_PROMPT", min_length=1, repr=False)
    ] = None
    reduce_sys_prompt: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="REDUCE_SYS_PROMPT", min_length=1, repr=False)
    ] = None
    community_level: typing.Annotated[
        typing.Optional[int],
        pydantic.Field(..., env="COMMUNITY_LEVEL", ge=0)
    ] = None
    allow_general_knowledge: typing.Annotated[
        typing.Optional[bool],
        pydantic.Field(..., env="ALLOW_GENERAL_KNOWLEDGE")
    ] = None
    general_knowledge_sys_prompt: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="GENERAL_KNOWLEDGE_SYS_PROMPT", min_length=1, repr=False)
    ] = None
    no_data_answer: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="NO_DATA_ANSWER", min_length=1)
    ] = None
    json_mode: typing.Annotated[
        typing.Optional[bool],
        pydantic.Field(..., env="JSON_MODE")
    ] = None
    max_data_tokens: typing.Annotated[
        typing.Optional[int],
        pydantic.Field(..., env="MAX_DATA_TOKENS", ge=1)
    ] = None
    encoding_model: typing.Annotated[
        typing.Optional[str],
        pydantic.Field(..., env="ENCODING_MODEL", min_length=1)
    ] = None
    kwargs: typing.Annotated[
        typing.Optional[typing.Dict[str, typing.Any]],
        pydantic.Field(..., env="KWARGS")
    ] = None

    @pydantic.field_serializer(
        'map_sys_prompt',
        'reduce_sys_prompt',
        'general_knowledge_sys_prompt'
    )
    def __serialize_prompt(self, prompt: typing.Optional[str]) -> typing.Optional[str]:
        return prompt[:50] + '...' if prompt and len(prompt) > 50 else prompt


class GraphRAGConfig(pydantic_settings.BaseSettings):
    chat_llm: ChatLLMConfig
    embedding: EmbeddingConfig
    logging: LoggingConfig
    context: ContextConfig
    local_search: LocalSearchConfig
    global_search: GlobalSearchConfig

    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix='GRAPHRAG_QUERY__',
        validate_default=False,
        env_nested_delimiter='__',
        env_file='.env',
        extra='ignore',
    )

    @classmethod
    def from_config_file(
        cls,
        config_file: typing.Union[str, os.PathLike[str], pathlib.Path],
        **kwargs: typing.Any,
    ) -> GraphRAGConfig:
        """
        Loads the configuration from a file. The file format is determined by
        the file extension.

        Supported file formats: JSON (.json), TOML (.toml), YAML (.yaml, .yml).

        Args:
            config_file: Path to the configuration file.
            **kwargs: Additional keyword arguments to pass to the constructor.

        Returns:
            GraphRAGConfig: The configuration object initialized from the file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If the file format is unsupported.
            ImportError:
                If the required package for reading the file format is not
                installed.
        """
        config_file_ = pathlib.Path(config_file)
        if not config_file_.exists():
            raise FileNotFoundError(f"Config file not found: {config_file_}")

        if config_file_.suffix not in ['.json', '.toml', '.yaml', '.yml']:
            raise ValueError(f"Unsupported config file format: {config_file_.suffix}")

        if config_file_.suffix == '.json':
            import json
            with open(config_file_, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
        elif config_file_.suffix == '.toml':
            try:
                import toml
            except ImportError:
                raise ImportError("Please install the 'toml' package to read TOML files.")
            with open(config_file_, 'r', encoding='utf-8') as f:
                config_dict = toml.load(f)
        else:
            try:
                import yaml
            except ImportError:
                raise ImportError("Please install the 'pyyaml' package to read YAML files.")
            with open(config_file_, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)

        return cls(**config_dict, **kwargs)

    def __init__(self, **kwargs: typing.Any) -> None:
        """
        Initializes the GraphRAGConfig object, ensuring all required fields are
        present.

        Args:
            **kwargs: Configuration parameters for initialization.

        Raises:
            GraphRAGWarning: If a required field is missing or invalid.
        """
        # Ensure all fields are present
        for field in self.__fields__.keys():
            if (field not in kwargs or not isinstance(kwargs[field], dict)
                    and not isinstance(kwargs[field], pydantic.BaseModel)):
                warnings.warn(
                    f"Missing or invalid field: {field}, initializing to empty dict",
                    _errors.GraphRAGWarning,
                )
                kwargs[field] = {}
        super().__init__(**kwargs)
