# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""System prompts for global search."""

MAP_SYSTEM_PROMPT = """
You are a helpful assistant responding to questions about data in the tables provided.
"""

MAP_USER_PROMPT = """
===============
Generate a response consisting of a list of key points that responds to the user's question, summarizing all relevant information in the input data tables.
You should use the data provided in the data tables below as the primary context for generating the response.
If you don't know the answer or if the input data tables do not contain sufficient information to provide an answer, just say so. Do not make anything up.

Each key point in the response should have the following element:
- Description: A comprehensive description of the point.
- Importance Score: An integer score between 0-100 that indicates how important the point is in answering the user's question. An 'I don't know' type of response should have a score of 0.

The response MUST be JSON formatted as follows:
{{
    "points": [
        {{"description": "Description of point 1 [Data: Reports (report ids)]", "score": score_value}},
        {{"description": "Description of point 2 [Data: Reports (report ids)]", "score": score_value}}
    ]
}}


The response shall preserve the original meaning and use of modal verbs such as "shall", "may" or "will".

Points supported by data should list the relevant reports as references as follows:
"This is an example sentence supported by data references [Data: Reports (report ids)]"

**Do not list more than 5 record ids in a single reference**. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

===============
For example:
user question: Is Person X currently under investigation for alleged illegal activities or unethical behavior?
---Data Tables---
| id | title                                | occurrence weight | content | rank |
|----|--------------------------------------|-------------------|---------|------|
| 1  | Allegations against Person X   | 1                 | Allegations of financial misconduct           |   4.0   |
| 2  | Allegations against Person X   | 0.3                 | Allegations of unethical business practices   |   4.0   |
| 3  | Allegations against Person X   | 0.8               | Allegations of workplace harassment          |   3.0   |
| 4  | CEO of company X               | 1                 | Person X is CEO of Company X             |   3.0   |
| 5  | owner of company Y              | 1                 | Person X is the owner of Company Y     |   3.0   |

answer:
{{
    "points": [
        {{"description": "Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Reports (1, 2, 3, 4)].", "score": 85}},
        {{"description": "He is also CEO of company X [Data: Reports (6)]", "score": 75}}
    ]
}}

==============
user question: {user_question}

---Data tables---
{context_data}

answer:
"""
