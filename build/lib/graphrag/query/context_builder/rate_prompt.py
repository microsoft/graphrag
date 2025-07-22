# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Global search with dynamic community selection prompt."""

RATE_QUERY = """
---Role---
You are a helpful assistant responsible for deciding whether the provided information is useful in answering a given question, even if it is only partially relevant.
---Goal---
On a scale from 0 to 5, please rate how relevant or helpful is the provided information in answering the question.
---Information---
{description}
---Question---
{question}
---Target response length and format---
Please response in the following JSON format with two entries:
- "reason": the reasoning of your rating, please include information that you have considered.
- "rating": the relevancy rating from 0 to 5, where 0 is the least relevant and 5 is the most relevant.
{{
    "reason": str,
    "rating": int.
}}
"""
