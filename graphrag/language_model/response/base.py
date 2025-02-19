# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Base llm response protocol."""

from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel, covariant=True)


class ModelOutput(Protocol):
    """Protocol for Model response's output object."""

    @property
    def content(self) -> str:
        """Return the textual content of the output."""
        ...


class ModelResponse(Protocol, Generic[T]):
    """Protocol for LLM response."""

    @property
    def output(self) -> ModelOutput:
        """Return the output of the response."""
        ...

    @property
    def parsed_response(self) -> T | None:
        """Return the parsed response."""
        ...

    @property
    def history(self) -> list:
        """Return the history of the response."""
        ...


class BaseModelOutput(BaseModel):
    """Base class for LLM output."""

    content: str = Field(..., description="The textual content of the output.")
    """The textual content of the output."""


class BaseModelResponse(BaseModel, Generic[T]):
    """Base class for a Model response."""

    output: BaseModelOutput
    """"""
    parsed_response: T | None = None
    """Parsed response."""
    history: list[Any] = Field(default_factory=list)
    """History of the response."""
    tool_calls: list = Field(default_factory=list)
    """Tool calls required by the Model. These will be instances of the LLM tools (with filled parameters)."""
    metrics: Any | None = None
    """Request/response metrics."""
    cache_hit: bool | None = None
    """Whether the response was a cache hit."""
