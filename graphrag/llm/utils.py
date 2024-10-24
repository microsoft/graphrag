# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utility functions for the OpenAI API."""

import json
import logging
import re
from collections.abc import Callable
from typing import Any

import tiktoken
from json_repair import repair_json
from openai import (
    APIConnectionError,
    InternalServerError,
    RateLimitError,
)

from .types import LLMConfig

DEFAULT_ENCODING = "cl100k_base"

_encoders: dict[str, tiktoken.Encoding] = {}

RETRYABLE_ERRORS: list[type[Exception]] = [
    RateLimitError,
    APIConnectionError,
    InternalServerError,
]
RATE_LIMIT_ERRORS: list[type[Exception]] = [RateLimitError]

log = logging.getLogger(__name__)


def get_token_counter(config: LLMConfig) -> Callable[[str], int]:
    """Get a function that counts the number of tokens in a string."""
    model = config.encoding_model or "cl100k_base"
    enc = _encoders.get(model)
    if enc is None:
        enc = tiktoken.get_encoding(model)
        _encoders[model] = enc

    return lambda s: len(enc.encode(s))


def perform_variable_replacements(
    input: str, history: list[dict], variables: dict | None
) -> str:
    """Perform variable replacements on the input string and in a chat log."""
    result = input

    def replace_all(input: str) -> str:
        result = input
        if variables:
            for entry in variables:
                result = result.replace(f"{{{entry}}}", variables[entry])
        return result

    result = replace_all(result)
    for i in range(len(history)):
        entry = history[i]
        if entry.get("role") == "system":
            history[i]["content"] = replace_all(entry.get("content") or "")

    return result


def get_completion_llm_args(
    parameters: dict | None, configuration: LLMConfig
) -> dict:
    """Get the arguments for a completion LLM."""
    return {
        **configuration.get_completion_cache_args(),
        **(parameters or {}),
    }


def try_parse_json_object(input: str) -> tuple[str, dict]:
    """JSON cleaning and formatting utilities."""
    # Sometimes, the LLM returns a json string with some extra description, this function will clean it up.

    result = None
    try:
        # Try parse first
        result = json.loads(input)
    except json.JSONDecodeError:
        log.info("Warning: Error decoding faulty json, attempting repair")

    if result:
        return input, result

    _pattern = r"\{(.*)\}"
    _match = re.search(_pattern, input, re.DOTALL)
    input = "{" + _match.group(1) + "}" if _match else input

    # Clean up json string.
    input = (
        input.replace("{{", "{")
        .replace("}}", "}")
        .replace('"[{', "[{")
        .replace('}]"', "}]")
        .replace("\\", " ")
        .replace("\\n", " ")
        .replace("\n", " ")
        .replace("\r", "")
        .strip()
    )

    # Remove JSON Markdown Frame
    if input.startswith("```json"):
        input = input[len("```json") :]
    if input.endswith("```"):
        input = input[: len(input) - len("```")]

    try:
        result = json.loads(input)
    except json.JSONDecodeError:
        # Fixup potentially malformed json string using json_repair.
        input = str(repair_json(json_str=input, return_objects=False))

        # Generate JSON-string output using best-attempt prompting & parsing techniques.
        try:
            result = json.loads(input)
        except json.JSONDecodeError:
            log.exception("error loading json, json=%s", input)
            return input, {}
        else:
            if not isinstance(result, dict):
                log.exception("not expected dict type. type=%s:", type(result))
                return input, {}
            return input, result
    else:
        return input, result


def get_sleep_time_from_error(e: Any) -> float:
    """Extract the sleep time value from a RateLimitError. This is usually only available in Azure."""
    sleep_time = 0.0
    if isinstance(e, RateLimitError) and _please_retry_after in str(e):
        # could be second or seconds
        sleep_time = int(str(e).split(_please_retry_after)[1].split(" second")[0])

    return sleep_time


_please_retry_after = "Please retry after "


def non_blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return None if stripped == "" else value


def non_none_value_key(data: dict | None) -> dict:
    """Remove key from dict where value is None"""
    if data is None:
        return {}
    return {k: v for k, v in data.items() if v is not None}
