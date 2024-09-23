# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utility prompts for low-level LLM invocations."""

JSON_CHECK_PROMPT = """
You are going to be given a malformed JSON string that threw an error during json.loads.
It probably contains unnecessary escape sequences, or it is missing a comma or colon somewhere.
Your task is to fix this string and return a well-formed JSON string containing a single object.
Eliminate any unnecessary escape sequences.
Only return valid JSON, parseable with json.loads, without commentary.

# Examples
-----------
Text: {{ \\"title\\": \\"abc\\", \\"summary\\": \\"def\\" }}
Output: {{"title": "abc", "summary": "def"}}
-----------
Text: {{"title": "abc", "summary": "def"
Output: {{"title": "abc", "summary": "def"}}
-----------
Text: {{"title': "abc", 'summary": "def"
Output: {{"title": "abc", "summary": "def"}}
-----------
Text: "{{"title": "abc", "summary": "def"}}"
Output: {{"title": "abc", "summary": "def"}}
-----------
Text: [{{"title": "abc", "summary": "def"}}]
Output: [{{"title": "abc", "summary": "def"}}]
-----------
Text: [{{"title": "abc", "summary": "def"}}, {{ \\"title\\": \\"abc\\", \\"summary\\": \\"def\\" }}]
Output: [{{"title": "abc", "summary": "def"}}, {{"title": "abc", "summary": "def"}}]
-----------
Text: ```json\n[{{"title": "abc", "summary": "def"}}, {{ \\"title\\": \\"abc\\", \\"summary\\": \\"def\\" }}]```
Output: [{{"title": "abc", "summary": "def"}}, {{"title": "abc", "summary": "def"}}]


# Real Data
Text: {input_text}
Output:"""
