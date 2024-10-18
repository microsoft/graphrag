# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

from openai.types import chat

ChatCompletionMessageParam = chat.ChatCompletionMessageParam
ChatCompletion = chat.ChatCompletion
ChatCompletionChunk = chat.ChatCompletionChunk

MessageParam_T: typing.TypeAlias = typing.Iterable[ChatCompletionMessageParam]
ChatResponse_T: typing.TypeAlias = ChatCompletion
SyncChatStreamResponse_T: typing.TypeAlias = typing.Generator[ChatCompletionChunk, None, None]
AsyncChatStreamResponse_T: typing.TypeAlias = typing.AsyncGenerator[ChatCompletionChunk, None]

EmbeddingResponse_T: typing.TypeAlias = typing.List[float]
