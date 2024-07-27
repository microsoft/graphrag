from typing import Optional, Dict, List, Union, Literal

from pydantic import BaseModel


class ChatCompletionMessageParam(BaseModel):
    content: str
    role: str = "user"


class ResponseFormat(BaseModel):
    type: str


class ChatCompletionStreamOptionsParam(BaseModel):
    enable: bool


class ChatCompletionToolParam(BaseModel):
    name: str
    description: str


class CompletionCreateParamsBase(BaseModel):
    messages: List[ChatCompletionMessageParam]
    model: str
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, int]] = None
    logprobs: Optional[bool] = None
    max_tokens: Optional[int] = None
    n: Optional[int] = None
    parallel_tool_calls: bool = False
    presence_penalty: Optional[float] = None
    response_format: ResponseFormat = ResponseFormat(type="text")
    seed: Optional[int] = None
    service_tier: Optional[Literal["auto", "default"]] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    stream_options: Optional[Dict] = None
    temperature: Optional[float] = 0.0
    tools: List[ChatCompletionToolParam] = None
    top_logprobs: Optional[int] = None
    top_p: Optional[float] = None
    user: Optional[str] = None
