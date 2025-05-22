# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

from typing import Any

from pydantic import BaseModel

class BaseModelOutput(BaseModel):
    content: str
    full_response: dict[str, Any] | None = None

    def __init__(
        self,
        content: str,
        full_response: dict[str, Any] | None = None,
    ) -> None: ...
