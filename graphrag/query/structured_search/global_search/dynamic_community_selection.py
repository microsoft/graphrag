import numpy as np
from typing import Dict, Any
import tiktoken
import pandas as pd
import asyncio

from datashaper import TableContainer, VerbInput

from graphrag.model import CommunityReport
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.index.graph.extractors.community_reports import schemas
from graphrag.index.verbs.graph.report import restore_community_hierarchy

RATE_QUERY = """
You are a helpful assistant responsible for deciding whether the provided information 
is useful in answering a given question, even if it is only partially relevant.

On a scale from 1 to 5, please rate how relevant or helpful is the provided information in answering the question:
1 - Not relevant in any way to the question
2 - Potentially relevant to the question
3 - Relevant to the question
4 - Highly relevant to the question
5 - It directly answers to the question


#######
Information
{description}
######
Question
{question}
######
Please only return the rating value.
"""


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
    ):
        """
        Args:
            community_reports: list of community reports
            nodes: DataFrame containing final nodes to reconstruct community hierarchy
            llm: OpenAI language model
            token_encoder: token encoder
            keep_parent: keep the parent node if the child node is relevant (default: False)
            num_repeats: number of times to repeat the rating process for the same community (default: 1)
            use_logit_bias: use logit_bias to bias the output to the rating tokens (default: True)
        """
        self.community_reports = {
            report.community_id: report for report in community_reports
        }
        self.community_hierarchy: pd.DataFrame = restore_community_hierarchy(
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

    async def rate_community_report(
        self, query: str, description: str, **llm_kwargs: Any
    ) -> Dict[str, Any]:
        """
        Rate how relevant a community report is with respect to the query on a scale of 1 to 5.
        A rating of 1 indicates the community is not relevant to the query and a rating of 5
        indicates the community directly answers the query.

        Args:
            query: the query (or question) to rate against
            description: the community description to rate, it can be the community
                title, summary, or the full content.
        Returns:
            result: a dictionary containing
                decision: the rating of the community. In the case of multiple repeats,
                    the rating wit h the most vote is selected.
                decisions: list of ratings of size num_repeats
                llm_calls: number of calls to LLM
                prompt_tokens: number of tokens used in the LLM calls
        """
        result = {"llm_calls": 0, "prompt_tokens": 0, "decisions": []}
        messages = [
            {
                "role": "system",
                "content": RATE_QUERY.format(description=description, question=query),
            },
            {"role": "user", "content": query},
        ]
        for repeat in range(self.num_repeats):
            decision = await self.llm.agenerate(messages=messages, **llm_kwargs)
            result["decisions"].append(decision[0])
            result["llm_calls"] += 1
            result["prompt_tokens"] += len(
                self.token_encoder.encode(messages[0]["content"])
            )
            result["prompt_tokens"] += len(
                self.token_encoder.encode(messages[1]["content"])
            )
        # select the decision with the most votes
        options, counts = np.unique(result["decisions"], return_counts=True)
        result["decision"] = int(options[np.argmax(counts)])
        return result

    async def select(self, query: str) -> (list[CommunityReport], int, int):
        # get all communities at level 0
        queue = [
            report.community_id
            for report in self.community_reports.values()
            if report.level == "0"
        ]

        llm_calls, prompt_tokens = 0, 0
        relevant_communities = set()
        while queue:
            gather_results = await asyncio.gather(
                *[
                    self.rate_community_report(
                        query=query,
                        description=self.community_reports[community].full_content,
                        **self.llm_kwargs,
                    )
                    for community in queue
                ]
            )

            communities_to_rate = []
            for community, result in zip(queue, gather_results):
                decision = result["decision"]
                llm_calls += result["llm_calls"]
                prompt_tokens += result["prompt_tokens"]
                if decision > 1:
                    relevant_communities.add(community)
                    # find child nodes of the current node and append them to the queue
                    sub_communities = self.community_hierarchy.loc[
                        self.community_hierarchy.community == community
                    ][schemas.SUB_COMMUNITY]
                    for sub_community in sub_communities:
                        # TODO check why some sub_communities are NOT in report_df
                        if sub_community in self.community_reports:
                            communities_to_rate.append(sub_community)
                    # remove parent node since the current node is deemed relevant
                    if not self.keep_parent:
                        parent_community = self.community_hierarchy.loc[
                            self.community_hierarchy[schemas.SUB_COMMUNITY] == community
                        ]
                        if len(parent_community):
                            assert len(parent_community) == 1
                            relevant_communities.discard(
                                parent_community.iloc[0].community
                            )
            queue = communities_to_rate

        community_reports = [
            self.community_reports[community] for community in relevant_communities
        ]

        return community_reports, llm_calls, prompt_tokens
