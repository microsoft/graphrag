import json
import logging
from typing import Optional, Dict, Any, List


log = logging.getLogger(__name__)


class DriftAction:
    """
    Represents an action containing query, answer, score, and follow-up actions.
    We want to be able to encapsulate the action strings being produced by the LLM in a clean way.
    """

    def __init__(self, query: str, answer: str | None = None, follow_ups: List['DriftAction'] | List[str] = []):
        self.query = query
        self.answer: str | None = answer  # corresponds to an 'intermediate_answer'
        self.score: Optional[float] = None
        self.follow_ups: List['DriftAction'] | List[str] = follow_ups
        self.metadata: Dict[str, Any] = {}
        # Should contain metadata explaining how to execute the action. Will not always be local search in the future.

    @property
    def is_complete(self) -> bool:
        return self.answer is not None

    def search(self, search_engine: Any, scorer: Any = None):
        raise NotImplementedError("Search method not implemented for DriftAction. Use asearch instead.")

    async def asearch(self, search_engine: Any, global_query:str, scorer: Any = None):
        # TODO: test that graph stores actions as reference... This SHOULD update the graph object.
        search_result = await search_engine.asearch(drift_query=global_query, query=self.query)
        try:
            response = json.loads(search_result.response)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse response: {search_result.response}. Ensure it is JSON serializable.")
        self.answer = response.pop('response', None)
        self.score = response.pop('score', float('-inf'))
        self.metadata.update({'context_data':search_result.context_data})
    
        self.follow_ups = response.pop('follow_up_queries', [])
        if self.follow_ups == []:
            log.warning("No follow-up actions found for response: %s", response)
            
        if scorer:
            self.compute_score(scorer)
        return self

    def compute_score(self, scorer: Any):
        score = scorer.compute_score(self.query, self.answer)
        self.score = score if score is not None else float('-inf')  # use -inf to help with sorting later

    def serialize(self, include_follow_ups: bool = True) -> Dict[str, Any]:
        """
        Serializes the action to a dictionary.
        """
        data = {
            'query': self.query,
            'answer': self.answer,
            'score': self.score,
            'metadata': self.metadata,
        }
        if include_follow_ups:
            data['follow_ups'] = [action.serialize() for action in self.follow_ups] # TODO: handle leftover string followups
        return data

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'DriftAction':
        """
        Deserializes the action from a dictionary.
        """
        action = cls(data['query'])
        action.answer = data.get('answer')
        action.score = data.get('score')
        action.metadata = data.get('metadata', {})
        if 'follow_ups' in data:
            action.follow_ups = [cls.deserialize(fu_data) for fu_data in data.get('follow_up_queries', [])]
        else:
            action.follow_ups = []
        return action

    @classmethod
    def from_primer_response(cls, query: str, response: str | Dict[str, Any] | List[Dict[str, Any]]) -> 'DriftAction':
        """
        Creates a DriftAction from the DRIFTPrimer response.
        """
        if isinstance(response, dict):
            action = cls(query, follow_ups=response.get('follow_up_queries', []), answer=response.get('intermediate_answer'))
            action.answer = response.get('intermediate_answer')
            action.score = response.get('score')
            return action
        else:
            raise ValueError(f'Response must be a dictionary. Found: {type(response)}'
                             f' with content: {response}')

    def __hash__(self):
        # Necessary for storing in networkx.MultiDiGraph. Assumes unique queries.
        return hash(self.query)

    def __eq__(self, other):
        return isinstance(other, DriftAction) and self.query == other.query
