# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A file containing prompts definition."""

SUMMARIZE_PROMPT = """
Write a concise, high-density working-memory summary for downstream QA.
Use ONLY the provided descriptions. Do not invent facts.

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

Write in third person and include entity names.
Limit output to {max_length} words.
Output exactly these sections:
- Current State
- Key Changes
- Decisions & Rationale
- Constraints / Preferences / Assumptions
- Open Issues / Next Actions
- Entity-Relationship Highlights
- Facts vs Inferences

#######
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""
