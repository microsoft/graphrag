# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""DRIFT Search Query State."""

import json
import logging
from typing import Any

from graphrag.query.llm.text_utils import try_parse_json_object

log = logging.getLogger(__name__)


class DriftAction:
    """
    Represent an action containing a query, answer, score, and follow-up actions.

    This class encapsulates action strings produced by the LLM in a structured way.
    """

    def __init__(
        self,
        query: str,
        answer: str | None = None,
        follow_ups: list["DriftAction"] | None = None,
    ):
        """
        Initialize the DriftAction with a query, optional answer, and follow-up actions.

        Args:
            query (str): The query for the action.
            answer (Optional[str]): The answer to the query, if available.
            follow_ups (Optional[list[DriftAction]]): A list of follow-up actions.
        """
        self.query = query
        self.answer: str | None = answer  # Corresponds to an 'intermediate_answer'
        self.score: float | None = None
        self.follow_ups: list[DriftAction] = (
            follow_ups if follow_ups is not None else []
        )
        self.metadata: dict[str, Any] = {
            "llm_calls": 0,
            "prompt_tokens": 0,
            "output_tokens": 0,
        }

    @property
    def is_complete(self) -> bool:
        """Check if the action is complete (i.e., an answer is available)."""
        return self.answer is not None

    async def search(self, search_engine: Any, global_query: str, scorer: Any = None):
        """
        Execute an asynchronous search using the search engine, and update the action with the results.

        If a scorer is provided, compute the score for the action.

        Args:
            search_engine (Any): The search engine to execute the query.
            global_query (str): The global query string.
            scorer (Any, optional): Scorer to compute scores for the action.

        Returns
        -------
        self : DriftAction
            Updated action with search results.
        """
        if self.is_complete:
            log.warning("Action already complete. Skipping search.")
            return self

        search_result = await search_engine.search(
            drift_query=global_query, query=self.query
        )

        # Do not launch exception as it will roll up with other steps
        # Instead return an empty response and let score -inf handle it
        _, response = try_parse_json_object(search_result.response, verbose=False)

        self.answer = response.pop("response", None)
        self.score = float(response.pop("score", "-inf"))
        self.metadata.update({"context_data": search_result.context_data})

        if self.answer is None:
            log.warning("No answer found for query: %s", self.query)

        self.metadata["llm_calls"] += 1
        self.metadata["prompt_tokens"] += search_result.prompt_tokens
        self.metadata["output_tokens"] += search_result.output_tokens

        self.follow_ups = response.pop("follow_up_queries", [])
        if not self.follow_ups:
            log.warning("No follow-up actions found for response: %s", response)

        if scorer:
            self.compute_score(scorer)

        return self

    def compute_score(self, scorer: Any):
        """
        Compute the score for the action using the provided scorer.

        Args:
            scorer (Any): The scorer to compute the score.
        """
        score = scorer.compute_score(self.query, self.answer)
        self.score = (
            score if score is not None else float("-inf")
        )  # Default to -inf for sorting

    def serialize(self, include_follow_ups: bool = True) -> dict[str, Any]:
        """
        Serialize the action to a dictionary.

        Args:
            include_follow_ups (bool): Whether to include follow-up actions in the serialization.

        Returns
        -------
        dict[str, Any]
            Serialized action as a dictionary.
        """
        data = {
            "query": self.query,
            "answer": self.answer,
            "score": self.score,
            "metadata": self.metadata,
        }
        if include_follow_ups:
            data["follow_ups"] = [action.serialize() for action in self.follow_ups]
        return data

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "DriftAction":
        """
        Deserialize the action from a dictionary.

        Args:
            data (dict[str, Any]): Serialized action data.

        Returns
        -------
        DriftAction
            A deserialized instance of DriftAction.
        """
        # Ensure 'query' exists in the data, raise a ValueError if missing
        query = data.get("query")
        if query is None:
            error_message = "Missing 'query' key in serialized data"
            raise ValueError(error_message)

        # Initialize the DriftAction
        action = cls(query)
        action.answer = data.get("answer")
        action.score = data.get("score")
        action.metadata = data.get("metadata", {})

        action.follow_ups = [
            cls.deserialize(fu_data) for fu_data in data.get("follow_up_queries", [])
        ]
        return action

    @classmethod
    def from_primer_response(
        cls, query: str, response: str | dict[str, Any] | list[dict[str, Any]]
    ) -> "DriftAction":
        """
        Create a DriftAction from a DRIFTPrimer response.

        Args:
            query (str): The query string.
            response (str | dict[str, Any] | list[dict[str, Any]]): Primer response data.

        Returns
        -------
        DriftAction
            A new instance of DriftAction based on the response.

        Raises
        ------
        ValueError
            If the response is not a dictionary or expected format.
        """
        if isinstance(response, dict):
            action = cls(
                query,
                follow_ups=response.get("follow_up_queries", []),
                answer=response.get("intermediate_answer"),
            )
            action.score = response.get("score")
            return action

        # If response is a string, attempt to parse as JSON
        if isinstance(response, str):
            try:
                parsed_response = json.loads(response)
                if isinstance(parsed_response, dict):
                    return cls.from_primer_response(query, parsed_response)
                error_message = "Parsed response must be a dictionary."
                raise ValueError(error_message)
            except json.JSONDecodeError as e:
                error_message = f"Failed to parse response string: {e}. Parsed response must be a dictionary."
                raise ValueError(error_message) from e

        error_message = f"Unsupported response type: {type(response).__name__}. Expected a dictionary or JSON string."
        raise ValueError(error_message)

    def __hash__(self) -> int:
        """
        Allow DriftAction objects to be hashable for use in networkx.MultiDiGraph.

        Assumes queries are unique.

        Returns
        -------
        int
            Hash based on the query.
        """
        return hash(self.query)

    def __eq__(self, other: object) -> bool:
        """
        Check equality based on the query string.

        Args:
            other (Any): Another object to compare with.

        Returns
        -------
        bool
            True if the other object is a DriftAction with the same query, False otherwise.
        """
        if not isinstance(other, DriftAction):
            return False
        return self.query == other.query
