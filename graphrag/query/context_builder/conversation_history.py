# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Classes for storing and managing conversation history."""

from dataclasses import dataclass
from enum import Enum

import pandas as pd
import tiktoken

from graphrag.query.llm.text_utils import num_tokens

"""
Enum for conversation roles
"""


class ConversationRole(str, Enum):
    """Enum for conversation roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    @staticmethod
    def from_string(value: str) -> "ConversationRole":
        """Convert string to ConversationRole."""
        if value == "system":
            return ConversationRole.SYSTEM
        if value == "user":
            return ConversationRole.USER
        if value == "assistant":
            return ConversationRole.ASSISTANT

        msg = f"Invalid Role: {value}"
        raise ValueError(msg)

    def __str__(self) -> str:
        """Return string representation of the enum value."""
        return self.value


"""
Data class for storing a single conversation turn
"""


@dataclass
class ConversationTurn:
    """Data class for storing a single conversation turn."""

    role: ConversationRole
    content: str

    def __str__(self) -> str:
        """Return string representation of the conversation turn."""
        return f"{self.role}: {self.content}"


@dataclass
class QATurn:
    """
    Data class for storing a QA turn.

    A QA turn contains a user question and one more multiple assistant answers.
    """

    user_query: ConversationTurn
    assistant_answers: list[ConversationTurn] | None = None

    def get_answer_text(self) -> str | None:
        """Get the text of the assistant answers."""
        return (
            "\n".join([answer.content for answer in self.assistant_answers])
            if self.assistant_answers
            else None
        )

    def __str__(self) -> str:
        """Return string representation of the QA turn."""
        answers = self.get_answer_text()
        return (
            f"Question: {self.user_query.content}\nAnswer: {answers}"
            if answers
            else f"Question: {self.user_query.content}"
        )


class ConversationHistory:
    """Class for storing a conversation history."""

    turns: list[ConversationTurn]

    def __init__(self):
        self.turns = []

    @classmethod
    def from_list(
        cls, conversation_turns: list[dict[str, str]]
    ) -> "ConversationHistory":
        """
        Create a conversation history from a list of conversation turns.

        Each turn is a dictionary in the form of {"role": "<conversation_role>", "content": "<turn content>"}
        """
        history = cls()
        for turn in conversation_turns:
            history.turns.append(
                ConversationTurn(
                    role=ConversationRole.from_string(
                        turn.get("role", ConversationRole.USER)
                    ),
                    content=turn.get("content", ""),
                )
            )
        return history

    def add_turn(self, role: ConversationRole, content: str):
        """Add a new turn to the conversation history."""
        self.turns.append(ConversationTurn(role=role, content=content))

    def to_qa_turns(self) -> list[QATurn]:
        """Convert conversation history to a list of QA turns."""
        qa_turns = list[QATurn]()
        current_qa_turn = None
        for turn in self.turns:
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

    def get_user_turns(self, max_user_turns: int | None = 1) -> list[str]:
        """Get the last user turns in the conversation history."""
        user_turns = []
        for turn in self.turns[::-1]:
            if turn.role == ConversationRole.USER:
                user_turns.append(turn.content)
                if max_user_turns and len(user_turns) >= max_user_turns:
                    break
        return user_turns

    def build_context(
        self,
        token_encoder: tiktoken.Encoding | None = None,
        include_user_turns_only: bool = True,
        max_qa_turns: int | None = 5,
        max_context_tokens: int = 8000,
        recency_bias: bool = True,
        column_delimiter: str = "|",
        context_name: str = "Conversation History",
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """
        Prepare conversation history as context data for system prompt.

        Parameters
        ----------
            user_queries_only: If True, only user queries (not assistant responses) will be included in the context, default is True.
            max_qa_turns: Maximum number of QA turns to include in the context, default is 1.
            recency_bias: If True, reverse the order of the conversation history to ensure last QA got prioritized.
            column_delimiter: Delimiter to use for separating columns in the context data, default is "|".
            context_name: Name of the context, default is "Conversation History".

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
            return ("", {context_name: pd.DataFrame()})

        # add table header
        header = f"-----{context_name}-----" + "\n"

        turn_list = []
        current_context_df = pd.DataFrame()
        for turn in qa_turns:
            turn_list.append({
                "turn": ConversationRole.USER.__str__(),
                "content": turn.user_query.content,
            })
            if turn.assistant_answers:
                turn_list.append({
                    "turn": ConversationRole.ASSISTANT.__str__(),
                    "content": turn.get_answer_text(),
                })

            context_df = pd.DataFrame(turn_list)
            context_text = header + context_df.to_csv(sep=column_delimiter, index=False)
            if num_tokens(context_text, token_encoder) > max_context_tokens:
                break

            current_context_df = context_df
        context_text = header + current_context_df.to_csv(
            sep=column_delimiter, index=False
        )
        return (context_text, {context_name.lower(): current_context_df})
