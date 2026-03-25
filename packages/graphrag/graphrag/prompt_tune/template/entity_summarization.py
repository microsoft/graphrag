# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Fine-tuning prompts for entity summarization."""

ENTITY_SUMMARIZATION_PROMPT = """
{persona}
Generate a concise, high-density working-memory summary in {language} for downstream QA.
Use ONLY the provided text. Do not invent facts.

Goal:
- preserve what is most useful for follow-up questions
- keep entities, relationships, state changes, and decisions explicit
- keep the latest valid information as current state
- separate multiple topics, but keep cross-topic links when they matter

Selection priority (combined):
1) recency/current validity
2) explicit corrections and decisions
3) QA relevance
4) entity/relationship connectedness
5) key dates, numbers, versions, named entities

Conflict rules:
- If statements conflict, keep the most recent or explicitly corrected statement as current.
- Keep older conflicting statements only as short history (example: "previously A -> corrected to B").
- For time ordering, use metadata timestamp first, then turn/order index, then textual cues.

Evidence rules:
- Mark direct facts vs inferred links.
- Use cautious wording for uncertain inference.
- Include only information grounded in the provided text.

Write in third person and include entity names.
Use exactly these sections:
- Current State
- Key Changes
- Decisions & Rationale
- Constraints / Preferences / Assumptions
- Open Issues / Next Actions
- Entity-Relationship Highlights
- Facts vs Inferences

Section rules:
- If multiple topics exist, group bullets by topic label inside each section.
- In "Entity-Relationship Highlights", include:
  - key entities
  - key relations
  - notable events/state changes
  - cross-topic links (only if supported by the text)
- Use compact slots when possible:
  - Current State: [entity] [status=current] [time] [fact]
  - Key Changes: [entity] [from] -> [to] [time] [reason(optional)]
  - Facts vs Inferences: FACT: ... / INFERENCE: ...

If no answer is possible, or the description is empty, only convey information provided within the text.
#######
-Data-
Entities: {{entity_name}}
Description List: {{description_list}}
#######
Output:"""
