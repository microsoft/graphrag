# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Contains algorithms to build context data for global search prompt."""

from typing import Any

import pandas as pd
import tiktoken

from graphrag.model import Community, CommunityReport, Entity
from graphrag.query.context_builder.community_context import (
    build_community_context,
)
from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from graphrag.query.context_builder.dynamic_community_selection import (
    DynamicCommunitySelection,
)
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.structured_search.base import GlobalContextBuilder


class GlobalCommunityContext(GlobalContextBuilder):
    """GlobalSearch community context builder."""

    def __init__(
        self,
        community_reports: list[CommunityReport],
        communities: list[Community],
        llm: ChatOpenAI,
        token_encoder: tiktoken.Encoding,
        entities: list[Entity] | None = None,
        dynamic_selection: bool = False,
        random_state: int = 86,
        concurrent_coroutines: int = 4,
    ):
        self.community_reports = community_reports
        self.entities = entities
        self.token_encoder = token_encoder
        self.dynamic_selection = None
        if dynamic_selection:
            self.dynamic_selection = DynamicCommunitySelection(
                community_reports=community_reports,
                communities=communities,
                llm=llm,
                token_encoder=token_encoder,
                keep_parent=False,
                concurrent_coroutines=concurrent_coroutines,
            )
        self.random_state = random_state

    async def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        use_community_summary: bool = True,
        column_delimiter: str = "|",
        shuffle_data: bool = True,
        include_community_rank: bool = False,
        min_community_rank: int = 0,
        community_rank_name: str = "rank",
        include_community_weight: bool = True,
        community_weight_name: str = "occurrence",
        normalize_community_weight: bool = True,
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

        community_reports = self.community_reports
        if self.dynamic_selection is not None:
            (
                community_reports,
                llm_calls,
                prompt_tokens,
            ) = await self.dynamic_selection.select(query)
            self.llm_calls += llm_calls
            self.prompt_tokens += prompt_tokens

        community_context, community_context_data = build_community_context(
            community_reports=community_reports,
            entities=self.entities,
            token_encoder=self.token_encoder,
            use_community_summary=use_community_summary,
            column_delimiter=column_delimiter,
            shuffle_data=shuffle_data,
            include_community_rank=include_community_rank,
            min_community_rank=min_community_rank,
            community_rank_name=community_rank_name,
            include_community_weight=include_community_weight,
            community_weight_name=community_weight_name,
            normalize_community_weight=normalize_community_weight,
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
