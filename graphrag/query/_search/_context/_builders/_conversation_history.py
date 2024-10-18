# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import collections
import dataclasses
import enum
import typing

import pandas as pd
import tiktoken

from .. import _types
from .... import _utils

ROLE__SYSTEM = "system"
ROLE__USER = "user"
ROLE__ASSISTANT = "assistant"


class ConversationRole(str, enum.Enum):
    # TODO: Use typing.Literal instead of string enum
    """Enum for conversation roles."""
    SYSTEM = ROLE__SYSTEM
    USER = ROLE__USER
    ASSISTANT = ROLE__ASSISTANT

    @staticmethod
    def from_string(value: str) -> "ConversationRole":
        """Convert string to ConversationRole."""
        if value == ROLE__SYSTEM:
            return ConversationRole.SYSTEM
        if value == ROLE__USER:
            return ConversationRole.USER
        if value == ROLE__ASSISTANT:
            return ConversationRole.ASSISTANT
        raise ValueError(f"Invalid Role: {value}")

    def __str__(self) -> str:
        return self.value


@dataclasses.dataclass
class ConversationTurn:
    """Data class for storing a single conversation turn."""

    role: ConversationRole
    content: str

    def __str__(self) -> str:
        """Return string representation of the conversation turn."""
        return f"{self.role}: {self.content}"


@dataclasses.dataclass
class QATurn:
    """
    Data class for storing a QA turn.

    A QA turn contains a user question and one more multiple assistant answers.
    """

    user_query: ConversationTurn
    assistant_answers: typing.Optional[typing.List[ConversationTurn]] = None

    def get_answer_text(self) -> typing.Optional[str]:
        """Get the text of the assistant answers."""
        return (
            "\n".join([answer.content for answer in self.assistant_answers])
            if self.assistant_answers else None
        )

    def __str__(self) -> str:
        """Return string representation of the QA turn."""
        answers = self.get_answer_text()
        return (
            f"Question: {self.user_query.content}\nAnswer: {answers}"
            if answers else f"Question: {self.user_query.content}"
        )


class ConversationHistory:
    """
    ConversationHistory is a class for storing and managing conversation turns.
    It supports adding new conversation turns, converting the conversation
    history to different formats, and preparing it as context data for system
    prompts.

    Attributes:
        A deque of conversation turns, with an optional maximum length to limit
        the number of stored turns.
    """

    _turns: typing.Deque[ConversationTurn]

    def __init__(self, max_length: typing.Optional[int] = None) -> None:
        self._turns = collections.deque(maxlen=max_length)

    @classmethod
    def from_list(
        cls,
        conversation_turns: typing.List[typing.Dict[typing.Literal["role", "content"], str]],
        max_length: typing.Optional[int] = None,
    ) -> typing.Self:
        """
        Creates a ConversationHistory instance from a list of conversation
        turns.

        Args:
            conversation_turns:
                A list of conversation turns where each turn is represented as
                a dictionary with keys "role" (the role of the speaker, such as
                user or assistant) and "content" (the content of the turn).
            max_length:
                An optional maximum length for the conversation history deque.
                If provided, limits the number of turns that can be stored.

        Returns:
            A new instance of ConversationHistory with the provided turns.
        """
        history = cls(max_length=max_length)
        for turn in conversation_turns:
            history.add_turn(
                role=ConversationRole.from_string(turn["role"]),
                content=turn["content"],
            )
        return history

    def add_turn(self, role: ConversationRole, content: str) -> None:
        """Add a new turn to the conversation history."""
        self._turns.append(ConversationTurn(role=role, content=content))

    def to_qa_turns(self) -> typing.List[QATurn]:
        """
        Converts the conversation history into a list of QA turns (user query
        and assistant responses).

        Returns:
            A list of QATurn objects representing the conversation as a series
            of user queries and corresponding assistant answers.
        """
        qa_turns: typing.List[QATurn] = []
        current_qa_turn = None
        for turn in self._turns:
            if turn.role == ConversationRole.USER:
                if current_qa_turn:
                    qa_turns.append(current_qa_turn)
                current_qa_turn = QATurn(user_query=turn, assistant_answers=[])
            else:
                if current_qa_turn:
                    current_qa_turn.assistant_answers.append(turn)  # type: ignore
        if current_qa_turn:
            qa_turns.append(current_qa_turn)
        return qa_turns

    def get_user_turns(self, max_user_turns: int = 1) -> typing.List[str]:
        """
        Retrieves the last user turns from the conversation history.

        Args:
            max_user_turns: The maximum number of user turns to retrieve.

        Returns:
            A list of strings representing the content of the last user turns.
        """
        return [turn.content
                for turn in list(self._turns)
                if turn.role == ConversationRole.USER][-max_user_turns:]

    def get_all_turns(self, max_turns: int = 10) -> typing.List[str]:
        """
        Retrieves all turns from the conversation history, up to the specified maximum.

        Args:
            max_turns: The maximum number of turns to retrieve.

        Returns:
            A list of strings representing the content of the turns.
        """
        return [turn.content for turn in list(self._turns)[-max_turns:]]

    def build_context(
        self,
        token_encoder: typing.Optional[tiktoken.Encoding] = None,
        include_user_turns_only: bool = True,
        max_qa_turns: int = 5,
        data_max_tokens: int = 8000,
        recency_bias: bool = True,
        column_delimiter: str = "|",
        context_name: str = "Conversation History",
    ) -> _types.SingleContext_T:
        """
        Prepares the conversation history as context data for system prompts.

        This method converts the conversation history into a structured context
        suitable for inclusion in system prompts, while respecting token limits
        and various formatting options.

        Args:
            token_encoder:
                An optional token encoder for calculating token counts.
            include_user_turns_only:
                If True, only include user turns in the context.
            max_qa_turns: The maximum number of QA turns to include.
            data_max_tokens:
                The maximum number of tokens allowed for the context data.
            recency_bias: If True, prioritize more recent conversation turns.
            column_delimiter:
                The delimiter used to separate columns in the context data.
            context_name:
                The name of the context section for conversation history.

        Returns:
            A tuple containing the context as a string and a dictionary with the
            context data as a DataFrame.
        """
        qa_turns = self.to_qa_turns()
        if include_user_turns_only:
            qa_turns = [
                QATurn(user_query=qa_turn.user_query, assistant_answers=None)
                for qa_turn in qa_turns
            ]
        if recency_bias:
            qa_turns = qa_turns[::-1]
        if max_qa_turns and len(qa_turns) > max_qa_turns:
            qa_turns = qa_turns[:max_qa_turns]

        # build context for qa turns
        # add context header
        if len(qa_turns) == 0 or not qa_turns:
            return "", {context_name: pd.DataFrame()}

        # add table header
        header = f"-----{context_name}-----" + "\n"

        turn_list = []
        current_context_df = pd.DataFrame()
        for turn in qa_turns:
            turn_list.append(
                {
                    "turn":    ConversationRole.USER.__str__(),
                    "content": turn.user_query.content,
                }
            )
            if turn.assistant_answers:
                turn_list.append(
                    {
                        "turn":    ConversationRole.ASSISTANT.__str__(),
                        "content": turn.get_answer_text() or "",
                    }
                )

            context_df = pd.DataFrame(turn_list)
            context_text = header + context_df.to_csv(sep=column_delimiter, index=False)
            if _utils.num_tokens(context_text, token_encoder) > data_max_tokens:
                break

            current_context_df = context_df
        context_text = header + current_context_df.to_csv(
            sep=column_delimiter, index=False
        )
        return context_text, {context_name.lower(): current_context_df}

    def to_dict(self) -> typing.List[typing.Dict[str, str]]:
        """
        Converts the conversation history into a list of dictionaries.

        Each dictionary represents a conversation turn, with the role (user or
        assistant) and the corresponding content.

        Returns:
            A list of dictionaries representing the conversation history.
        """
        return [{"role": turn.role.value, "content": turn.content} for turn in self._turns]
