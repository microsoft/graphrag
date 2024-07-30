import asyncio
from typing import Any

from pydantic import BaseModel


class TypedFuture(asyncio.Future):
    pass


class QuestionGenResult(BaseModel):
    questions: list[str]
    completion_time: float
    llm_calls: int
    prompt_tokens: int
