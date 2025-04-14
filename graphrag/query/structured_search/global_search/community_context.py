# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Contains algorithms to build context data for global search prompt."""

from typing import Any

import tiktoken

from graphrag.data_model.community import Community
from graphrag.data_model.community_report import CommunityReport
from graphrag.data_model.entity import Entity
from graphrag.query.context_builder.builders import ContextBuilderResult
from graphrag.query.context_builder.community_context import (
    build_community_context,
)
from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from graphrag.query.context_builder.dynamic_community_selection import (
    DynamicCommunitySelection,
)
from graphrag.query.structured_search.base import GlobalContextBuilder


class GlobalCommunityContext(GlobalContextBuilder):
    """GlobalSearch community context builder."""

    def __init__(
        self,
        community_reports: list[CommunityReport],
        communities: list[Community],
        entities: list[Entity] | None = None,
        token_encoder: tiktoken.Encoding | None = None,
        dynamic_community_selection: bool = False,
        dynamic_community_selection_kwargs: dict[str, Any] | None = None,
        random_state: int = 86,
    ):
        self.community_reports = community_reports
        self.entities = entities
        self.token_encoder = token_encoder
        self.dynamic_community_selection = None
        if dynamic_community_selection and isinstance(
            dynamic_community_selection_kwargs, dict
        ):
            self.dynamic_community_selection = DynamicCommunitySelection(
                community_reports=community_reports,
                communities=communities,
                model=dynamic_community_selection_kwargs.pop("model"),
                token_encoder=dynamic_community_selection_kwargs.pop("token_encoder"),
                **dynamic_community_selection_kwargs,
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
        max_context_tokens: int = 8000,
        context_name: str = "Reports",
        conversation_history_user_turns_only: bool = True,
        conversation_history_max_turns: int | None = 5,
        **kwargs: Any,
    ) -> ContextBuilderResult:
        """Prepare batches of community report data table as context data for global search."""
        conversation_history_context = ""
        final_context_data = {}
        llm_calls, prompt_tokens, output_tokens = 0, 0, 0
        if conversation_history:
            # build conversation history context
            (
                conversation_history_context,
                conversation_history_context_data,
            ) = conversation_history.build_context(
                include_user_turns_only=conversation_history_user_turns_only,
                max_qa_turns=conversation_history_max_turns,
                column_delimiter=column_delimiter,
                max_context_tokens=max_context_tokens,
                recency_bias=False,
            )
            if conversation_history_context != "":
                final_context_data = conversation_history_context_data

        community_reports = self.community_reports
        if self.dynamic_community_selection is not None:
            (
                community_reports,
                dynamic_info,
            ) = await self.dynamic_community_selection.select(query)
            llm_calls += dynamic_info["llm_calls"]
            prompt_tokens += dynamic_info["prompt_tokens"]
            output_tokens += dynamic_info["output_tokens"]

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
            max_context_tokens=max_context_tokens,
            single_batch=False,
            context_name=context_name,
            random_state=self.random_state,
        )

        # Prepare context_prefix based on whether conversation_history_context exists
        context_prefix = (
            f"{conversation_history_context}\n\n"
            if conversation_history_context
            else ""
        )

        final_context = (
            [f"{context_prefix}{context}" for context in community_context]
            if isinstance(community_context, list)
            else f"{context_prefix}{community_context}"
        )

        # Update the final context data with the provided community_context_data
        final_context_data.update(community_context_data)

        return ContextBuilderResult(
            context_chunks=final_context,
            context_records=final_context_data,
            llm_calls=llm_calls,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
        )
