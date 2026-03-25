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

Selection priority (combined):
1) recency/current validity
2) explicit corrections and decisions
3) QA relevance
4) entity/relationship connectedness
5) key dates, numbers, versions, named entities

Conflict rules:
- If statements conflict, keep the most recent or explicitly corrected statement as current.
- Keep older conflicting statements only as short history (example: "previously A -> corrected to B").

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

If no answer is possible, or the description is empty, only convey information provided within the text.
#######
-Data-
Entities: {{entity_name}}
Description List: {{description_list}}
#######
Output:"""
