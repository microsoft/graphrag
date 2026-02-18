# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A file containing prompts definition."""

ENTITY_RESOLUTION_PROMPT = """
You are an entity resolution expert. Below is a numbered list of entity names
extracted from a knowledge graph. Identify which names refer to the SAME
real-world entity and choose the best canonical name for each group of duplicates.

Rules:
- Only merge names that clearly refer to the same entity (e.g., "Ahab" and
"Captain Ahab", "USA" and "United States of America")
- Do NOT merge entities that are merely related (e.g., "Ahab" and "Moby Dick")
- Choose the most complete and commonly used name as the canonical form
- Reference entities by their number

Output format — one group per line, canonical number first, then duplicate numbers:
3, 17
5, 12, 28

Where each line means: all listed numbers refer to the same entity, and the
first number's name is the canonical form.

If no duplicates are found, respond with exactly: NO_DUPLICATES

Entity list:
{entity_list}
"""
