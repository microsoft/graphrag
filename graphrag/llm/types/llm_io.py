# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM Types."""

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from typing_extensions import NotRequired, TypedDict

from .llm_callbacks import IsResponseValidFn


class LLMInput(TypedDict):
    """The input of an LLM invocation."""

    name: NotRequired[str]
    """The name of the LLM invocation, if available."""

    json: NotRequired[bool]
    """If true, will attempt to elicit JSON from the LLM. Parsed JSON will be returned in the `json_output` field."""

    is_response_valid: NotRequired[IsResponseValidFn]
    """A function that checks if an LLM response is valid. Only valid if `json=True`."""

    variables: NotRequired[dict]
    """The variable replacements to use in the prompt."""

    history: NotRequired[list[dict] | None]
    """The history of the LLM invocation, if available (e.g. chat mode)"""

    model_parameters: NotRequired[dict]
    """Additional model parameters to use in the LLM invocation."""


T = TypeVar("T")


@dataclass
class LLMOutput(Generic[T]):
    """The output of an LLM invocation."""

    output: T | None
    """The output of the LLM invocation."""

    json: dict | None = field(default=None)
    """The JSON output from the LLM, if available."""

    history: list[dict] | None = field(default=None)
    """The history of the LLM invocation, if available (e.g. chat mode)"""
