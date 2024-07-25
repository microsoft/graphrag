from graphrag.llm.openai.openai_history_tracking_llm import OpenAIHistoryTrackingLLM
from graphrag.llm.mock.mock_completion_llm import MockCompletionLLM

async def test_history_tracking_llm() -> None:
  delegate = MockCompletionLLM(["response 1", "response 2"])
  llm = OpenAIHistoryTrackingLLM(delegate)

  response = await llm("input 1")
  assert len(response.history) == 2
  assert response.history[0] == {"role": "user", "content": "input 1"}
  assert response.history[1] == {"role": "system", "content": "response 1"}

  response = await llm("input 2", history=response.history)
  assert len(response.history) == 4
  assert response.history[0] == {"role": "user", "content": "input 1"}
  assert response.history[1] == {"role": "system", "content": "response 1"}
  assert response.history[2] == {"role": "user", "content": "input 2"}
  assert response.history[3] == {"role": "system", "content": "response 2"}
