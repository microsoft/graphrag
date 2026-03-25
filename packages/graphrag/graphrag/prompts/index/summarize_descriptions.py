# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A file containing prompts definition."""

SUMMARIZE_PROMPT = """
You are a helpful assistant responsible for generating a high-density working memory summary for downstream question-answering.
Given one or more entities and a list of descriptions related to the same entity or group of entities, produce a concise summary that preserves decision-relevant facts, temporal changes, and graph-usable relationships.

Prioritize information that is most useful for future QA:
- current state
- changes over time
- decisions and why they were made
- constraints, preferences, assumptions
- corrections and contradictions
- unresolved issues and next actions
- key numbers, dates, versions, and named entities

Conflict resolution rules:
1. If descriptions conflict, prefer the most recent or explicitly corrected information as the current state.
2. Do not keep contradictory statements with equal weight.
3. Keep older information only as compressed history when it is still useful (for example: "previously A, later corrected to B").

Evidence handling rules:
- Separate directly stated facts from inferred links.
- Do not overstate inferred links as certain facts.

Write in third person and include entity names for context.
Limit the final description length to {max_length} words.
Use the following compact structure:
- Current State:
- Key Changes (earlier -> later -> current):
- Decisions & Rationale:
- Constraints / Preferences / Assumptions:
- Unresolved Issues / Next Actions:
- Entity-Relationship Highlights:
- Facts vs Inferences:

#######
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""
