# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""ChatCompletionMessageParamBuilder class."""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Literal

from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import (
    ChatCompletionContentPartImageParam,
    ImageURL,
)
from openai.types.chat.chat_completion_content_part_input_audio_param import (
    ChatCompletionContentPartInputAudioParam,
    InputAudio,
)
from openai.types.chat.chat_completion_content_part_param import (
    ChatCompletionContentPartParam,
)
from openai.types.chat.chat_completion_content_part_text_param import (
    ChatCompletionContentPartTextParam,
)
from openai.types.chat.chat_completion_developer_message_param import (
    ChatCompletionDeveloperMessageParam,
)
from openai.types.chat.chat_completion_function_message_param import (
    ChatCompletionFunctionMessageParam,
)
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

if TYPE_CHECKING:
    from openai.types.chat.chat_completion_message_param import (
        ChatCompletionMessageParam,
    )

    from graphrag_llm.types import LLMCompletionMessagesParam


class CompletionMessagesBuilder:
    """CompletionMessagesBuilder class."""

    def __init__(self) -> None:
        """Initialize CompletionMessagesBuilder."""
        self._messages: list[ChatCompletionMessageParam] = []

    def add_system_message(
        self,
        content: str | Iterable[ChatCompletionContentPartTextParam],
        name: str | None = None,
    ) -> "CompletionMessagesBuilder":
        """Add system message.

        Parameters
        ----------
        content : str | Iterable[ChatCompletionContentPartTextParam]
            Content of the system message.
            If passing in Iterable[ChatCompletionContentPartTextParam], may use
            `CompletionContentPartBuilder` to build the content.
        name : str | None
            Optional name for the participant.

        Returns
        -------
        None
        """
        if name:
            self._messages.append(
                ChatCompletionSystemMessageParam(
                    role="system", content=content, name=name
                )
            )
        else:
            self._messages.append(
                ChatCompletionSystemMessageParam(role="system", content=content)
            )
        return self

    def add_developer_message(
        self,
        content: str | Iterable[ChatCompletionContentPartTextParam],
        name: str | None = None,
    ) -> "CompletionMessagesBuilder":
        """Add developer message.

        Parameters
        ----------
        content : str | Iterable[ChatCompletionContentPartTextParam]
            Content of the developer message.
            If passing in Iterable[ChatCompletionContentPartTextParam], may use
            `CompletionContentPartBuilder` to build the content.
        name : str | None
            Optional name for the participant.

        Returns
        -------
        None
        """
        if name:
            self._messages.append(
                ChatCompletionDeveloperMessageParam(
                    role="developer", content=content, name=name
                )
            )
        else:
            self._messages.append(
                ChatCompletionDeveloperMessageParam(role="developer", content=content)
            )

        return self

    def add_tool_message(
        self,
        content: str | Iterable[ChatCompletionContentPartTextParam],
        tool_call_id: str,
    ) -> "CompletionMessagesBuilder":
        """Add developer message.

        Parameters
        ----------
        content : str | Iterable[ChatCompletionContentPartTextParam]
            Content of the developer message.
            If passing in Iterable[ChatCompletionContentPartTextParam], may use
            `CompletionContentPartBuilder` to build the content.
        tool_call_id : str
            ID of the tool call that this message is responding to.

        Returns
        -------
        None
        """
        self._messages.append(
            ChatCompletionToolMessageParam(
                role="tool", content=content, tool_call_id=tool_call_id
            )
        )

        return self

    def add_function_message(
        self,
        function_name: str,
        content: str | None = None,
    ) -> "CompletionMessagesBuilder":
        """Add function message.

        Parameters
        ----------
        function_name : str
            Name of the function to call.
        content : str | None
            Content of the function message.

        Returns
        -------
        None
        """
        self._messages.append(
            ChatCompletionFunctionMessageParam(
                role="function", content=content, name=function_name
            )
        )

        return self

    def add_user_message(
        self,
        content: str | Iterable[ChatCompletionContentPartParam],
        name: str | None = None,
    ) -> "CompletionMessagesBuilder":
        """Add user message.

        Parameters
        ----------
        content : str | Iterable[ChatCompletionContentPartParam]
            Content of the user message.
            If passing in Iterable[ChatCompletionContentPartParam], may use
            `CompletionContentPartBuilder` to build the content.
        name : str | None
            Optional name for the participant.

        Returns
        -------
        None
        """
        if name:
            self._messages.append(
                ChatCompletionUserMessageParam(role="user", content=content, name=name)
            )
        else:
            self._messages.append(
                ChatCompletionUserMessageParam(role="user", content=content)
            )

        return self

    def add_assistant_message(
        self,
        message: str | ChatCompletionMessage,
        name: str | None = None,
    ) -> "CompletionMessagesBuilder":
        """Add assistant message.

        Parameters
        ----------
        message : ChatCompletionMessage
            Previous response message.
        name : str | None
            Optional name for the participant.

        Returns
        -------
        None
        """
        args = {
            "role": "assistant",
            "content": message if isinstance(message, str) else message.content,
            "refusal": None if isinstance(message, str) else message.refusal,
        }
        if name:
            args["name"] = name
        if not isinstance(message, str):
            if message.function_call:
                args["function_call"] = message.function_call
            if message.tool_calls:
                args["tool_calls"] = message.tool_calls
            if message.audio:
                args["audio"] = message.audio

        self._messages.append(ChatCompletionAssistantMessageParam(**args))

        return self

    def build(self) -> "LLMCompletionMessagesParam":
        """Get messages."""
        return self._messages


class CompletionContentPartBuilder:
    """CompletionContentPartBuilder class."""

    def __init__(self) -> None:
        """Initialize CompletionContentPartBuilder."""
        self._content_parts: list[ChatCompletionContentPartParam] = []

    def add_text_part(self, text: str) -> "CompletionContentPartBuilder":
        """Add text part.

        Parameters
        ----------
        text : str
            Text content.

        Returns
        -------
        None
        """
        self._content_parts.append(
            ChatCompletionContentPartTextParam(text=text, type="text")
        )
        return self

    def add_image_part(
        self, url: str, detail: Literal["auto", "low", "high"]
    ) -> "CompletionContentPartBuilder":
        """Add image part.

        Parameters
        ----------
        url : str
            Either an URL of the image or the base64 encoded image data.
        detail : Literal["auto", "low", "high"]
            Specifies the detail level of the image.

        Returns
        -------
        None
        """
        self._content_parts.append(
            ChatCompletionContentPartImageParam(
                image_url=ImageURL(url=url, detail=detail), type="image_url"
            )
        )
        return self

    def add_audio_part(
        self, data: str, _format: Literal["wav", "mp3"]
    ) -> "CompletionContentPartBuilder":
        """Add audio part.

        Parameters
        ----------
        data : str
            Base64 encoded audio data.
        _format : Literal["wav", "mp3"]
            The format of the encoded audio data. Currently supports "wav" and "mp3".

        Returns
        -------
        None
        """
        self._content_parts.append(
            ChatCompletionContentPartInputAudioParam(
                input_audio=InputAudio(data=data, format=_format), type="input_audio"
            )
        )
        return self

    def build(self) -> list[ChatCompletionContentPartParam]:
        """Get content parts.

        Returns
        -------
        list[ChatCompletionContentPartParam]
            List of content parts.
        """
        return self._content_parts
