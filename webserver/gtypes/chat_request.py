from dataclasses import Field
from typing import Optional, Dict, List, Union, Literal, Any

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

    def llm_chat_params(self) -> dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "stop": self.stop,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "logprobs": self.logprobs,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "response_format": self.response_format,
            "seed": self.seed,
            "service_tier": self.service_tier,
        }


class ChatQuestionGen(BaseModel):
    messages: List[ChatCompletionMessageParam]
    model: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.0
    n: Optional[int] = None


class Model(BaseModel):
    id: str
    object: Literal["model"]
    created: int
    owned_by: str


class ModelList(BaseModel):
    object: Literal["list"] = "list"
    data: List[Model]
