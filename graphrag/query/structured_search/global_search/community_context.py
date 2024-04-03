# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Contains algorithms to build context data for global search prompt."""

from typing import Any

import pandas as pd
import tiktoken

from graphrag.model import CommunityReport
from graphrag.query.context_builder.community_context import (
    build_community_context,
)
from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from graphrag.query.structured_search.base import GlobalContextBuilder


class GlobalCommunityContext(GlobalContextBuilder):
    """GlobalSearch community context builder."""

    def __init__(
        self,
        community_reports: list[CommunityReport],
        token_encoder: tiktoken.Encoding | None = None,
        random_state: int = 86,
    ):
        self.community_reports = community_reports
        self.token_encoder = token_encoder
        self.random_state = random_state

    def build_context(
        self,
        conversation_history: ConversationHistory | None = None,
        use_community_summary: bool = True,
        column_delimiter: str = "|",
        shuffle_data: bool = True,
        include_community_rank: bool = False,
        min_community_rank: int = 0,
        max_tokens: int = 8000,
        context_name: str = "Reports",
        conversation_history_user_turns_only: bool = True,
        conversation_history_max_turns: int | None = 5,
        **kwargs: Any,
    ) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
        """Prepare batches of community report data table as context data for global search."""
        conversation_history_context = ""
        final_context_data = {}
        if conversation_history:
            # build conversation history context
            (
                conversation_history_context,
                conversation_history_context_data,
            ) = conversation_history.build_context(
                include_user_turns_only=conversation_history_user_turns_only,
                max_qa_turns=conversation_history_max_turns,
                column_delimiter=column_delimiter,
                max_tokens=max_tokens,
                recency_bias=False,
            )
            if conversation_history_context != "":
                final_context_data = conversation_history_context_data

        community_context, community_context_data = build_community_context(
            community_reports=self.community_reports,
            token_encoder=self.token_encoder,
            use_community_summary=use_community_summary,
            column_delimiter=column_delimiter,
            shuffle_data=shuffle_data,
            include_community_rank=include_community_rank,
            min_community_rank=min_community_rank,
            max_tokens=max_tokens,
            single_batch=False,
            context_name=context_name,
            random_state=self.random_state,
        )
        if isinstance(community_context, list):
            final_context = [
                f"{conversation_history_context}\n\n{context}"
                for context in community_context
            ]
        else:
            final_context = f"{conversation_history_context}\n\n{community_context}"

        final_context_data.update(community_context_data)
        return (final_context, final_context_data)
