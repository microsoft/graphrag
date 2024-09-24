# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Algorithm to dynamically select relevant communities with respect to a query."""

import asyncio
import logging

import pandas as pd
import tiktoken
from datashaper import TableContainer, VerbInput
from collections import Counter
from graphrag.index.graph.extractors.community_reports import schemas
from graphrag.index.verbs.graph.report import restore_community_hierarchy
from graphrag.model import CommunityReport
from graphrag.query.context_builder.rate_relevancy import rate_relevancy
from graphrag.query.llm.oai.chat_openai import ChatOpenAI

log = logging.getLogger(__name__)


class DynamicCommunitySelection:
    """Dynamic community selection to select community reports that are relevant to the query."""

    def __init__(
        self,
        community_reports: list[CommunityReport],
        nodes: pd.DataFrame,
        llm: ChatOpenAI,
        token_encoder: tiktoken.Encoding,
        keep_parent: bool = False,
        num_repeats: int = 1,
        use_logit_bias: bool = True,
        concurrent_coroutines: int = 8,
    ):
        self.community_reports = {
            report.community_id: report for report in community_reports
        }
        self.community_hierarchy = restore_community_hierarchy(
            VerbInput(source=TableContainer(nodes))
        ).table
        self.llm = llm
        self.token_encoder = token_encoder
        self.keep_parent = keep_parent
        self.num_repeats = num_repeats
        self.llm_kwargs = {"temperature": 0.0, "max_tokens": 2}
        if use_logit_bias:
            # bias the output to the rating tokens
            self.llm_kwargs["logit_bias"] = {
                token_encoder.encode(token)[0]: 5 for token in ["1", "2", "3", "4", "5"]
            }
        self.semaphore = asyncio.Semaphore(concurrent_coroutines)

    async def select(self, query: str) -> tuple[list[CommunityReport], int, int]:
        """
        Select relevant communities with respect to the query.

        Args:
            query: the query to rate against
        """
        # get all communities at level 0
        queue = [
            report.community_id
            for report in self.community_reports.values()
            if report.level == "0"
        ]

        ratings = []  # store the ratings for each community
        llm_calls, prompt_tokens = 0, 0
        relevant_communities = set()
        while queue:
            gather_results = await asyncio.gather(
                *[
                    rate_relevancy(
                        query=query,
                        description=self.community_reports[community].full_content,
                        llm=self.llm,
                        token_encoder=self.token_encoder,
                        num_repeats=self.num_repeats,
                        semaphore=self.semaphore,
                        **self.llm_kwargs,
                    )
                    for community in queue
                ]
            )

            communities_to_rate = []
            for community, result in zip(queue, gather_results, strict=True):
                rating = result["rating"]
                ratings.append(rating)
                llm_calls += result["llm_calls"]
                prompt_tokens += result["prompt_tokens"]
                if rating > 1:
                    relevant_communities.add(community)
                    # find child nodes of the current node and append them to the queue
                    sub_communities = self.community_hierarchy.loc[
                        self.community_hierarchy.community == community
                    ][schemas.SUB_COMMUNITY]
                    # TODO check why some sub_communities are NOT in report_df
                    communities_to_rate.extend(
                        [
                            sub_community
                            for sub_community in sub_communities
                            if sub_community in self.community_reports
                        ]
                    )
                    # remove parent node since the current node is deemed relevant
                    if not self.keep_parent:
                        parent_community = self.community_hierarchy.loc[
                            self.community_hierarchy[schemas.SUB_COMMUNITY] == community
                        ]
                        if len(parent_community):
                            relevant_communities.discard(
                                parent_community.iloc[0].community
                            )
            queue = communities_to_rate

        community_reports = [
            self.community_reports[community] for community in relevant_communities
        ]

        log.debug(
            f"Dynamic community selection rating distribution: {dict(sorted(Counter(ratings).items()))}"
        )
        log.debug(
            f"Dynamic community selection: {len(relevant_communities)} out of {len(self.community_reports)} community reports are relevant."
        )

        return community_reports, llm_calls, prompt_tokens
