# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel

_T = TypeVar("_T", bound=BaseModel, covariant=True)

class ModelOutput(Protocol):
    @property
    def content(self) -> str: ...
    @property
    def full_response(self) -> dict[str, Any] | None: ...

class ModelResponse(Protocol, Generic[_T]):
    @property
    def output(self) -> ModelOutput: ...
    @property
    def parsed_response(self) -> _T | None: ...
    @property
    def history(self) -> list[Any]: ...

class BaseModelOutput(BaseModel):
    content: str
    full_response: dict[str, Any] | None

    def __init__(
        self,
        content: str,
        full_response: dict[str, Any] | None = None,
    ) -> None: ...

class BaseModelResponse(BaseModel, Generic[_T]):
    output: BaseModelOutput
    parsed_response: _T | None
    history: list[Any]
    tool_calls: list[Any]
    metrics: Any | None
    cache_hit: bool | None

    def __init__(
        self,
        output: BaseModelOutput,
        parsed_response: _T | None = None,
        history: list[Any] = ...,  # default provided by Pydantic
        tool_calls: list[Any] = ...,  # default provided by Pydantic
        metrics: Any | None = None,
        cache_hit: bool | None = None,
    ) -> None: ...
