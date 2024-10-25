# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""DRIFT Search prompts."""

DRIFT_LOCAL_SYSTEM_PROMPT = """
---Role---

You are a helpful assistant responding to questions about data in the tables provided.


---Goal---

Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.

If you don't know the answer, just say so. Do not make anything up.

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:

"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Sources (15, 16)]."

where 15, 16, 1, 5, 7, 23, 2, 7, 34, 46, and 64 represent the id (not the index) of the relevant data record.

Pay close attention specifically to the Sources tables as it contains the most relevant information for the user query. You will be rewarded for preserving the context of the sources in your response.

---Target response length and format---

{response_type}


---Data tables---

{context_data}


---Goal---

Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.

If you don't know the answer, just say so. Do not make anything up.

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:

"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Sources (15, 16)]."

where 15, 16, 1, 5, 7, 23, 2, 7, 34, 46, and 64 represent the id (not the index) of the relevant data record.

Pay close attention specifically to the Sources tables as it contains the most relevant information for the user query. You will be rewarded for preserving the context of the sources in your response.

---Target response length and format---

{response_type}

Add sections and commentary to the response as appropriate for the length and format.

Additionally provide a score between 0 and 100 representing how well the response addresses the overall research question: {global_query}. Based on your response, suggest up to five follow-up questions that could be asked to further explore the topic as it relates to the overall research question. Do not include scores or follow up questions in the 'response' field of the JSON, add them to the respective 'score' and 'follow_up_queries' keys of the JSON output. Format your response in JSON with the following keys and values:

{{'response': str, Put your answer, formatted in markdown, here. Do not answer the global query in this section.
'score': int,
'follow_up_queries': List[str]}}
"""


DRIFT_REDUCE_PROMPT = """
---Role---

You are a helpful assistant responding to questions about data in the reports provided.

---Goal---

Generate a response of the target length and format that responds to the user's question, summarizing all information in the input reports appropriate for the response length and format, and incorporating any relevant general knowledge while being as specific, accurate and concise as possible.

If you don't know the answer, just say so. Do not make anything up.

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:

"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Sources (1, 5, 15)]."

Do not include information where the supporting evidence for it is not provided.

If you decide to use general knowledge, you should add a delimiter stating that the information is not supported by the data tables. For example:

"Person X is the owner of Company Y and subject to many allegations of wrongdoing. [Data: General Knowledge (href)]"

---Data Reports---

{context_data}

---Target response length and format---

Multiple paragraphs


---Goal---

Generate a response of the target length and format that responds to the user's question, summarizing all information in the input reports appropriate for the response length and format, and incorporating any relevant general knowledge while being as specific, accurate and concise as possible.

If you don't know the answer, just say so. Do not make anything up.

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:

"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Sources (1, 5, 15)]."

Do not include information where the supporting evidence for it is not provided.

If you decide to use general knowledge, you should add a delimiter stating that the information is not supported by the data tables. For example:

"Person X is the owner of Company Y and subject to many allegations of wrongdoing. [Data: General Knowledge (href)]".

Add sections and commentary to the response as appropriate for the length and format. Style the response in markdown. Now answer the following query using the data above:

{query}

"""


DRIFT_PRIMER_PROMPT = """You are a helpful agent designed to reason over a knowledge graph in response to a user query.
This is a unique knowledge graph where edges are freeform text rather than verb operators. You will begin your reasoning looking at a summary of the content of the most relevant communites and will provide:

1. score: How well the intermediate answer addresses the query. A score of 0 indicates a poor, unfocused answer, while a score of 100 indicates a highly focused, relevant answer that addresses the query in its entirety.

2. intermediate_answer: This answer should match the level of detail and length found in the community summaries. The intermediate answer should be exactly 2000 characters long. This must be formatted in markdown and must begin with a header that explains how the following text is related to the query.

3. follow_up_queries: A list of follow-up queries that could be asked to further explore the topic. These should be formatted as a list of strings. Generate at least five good follow-up queries.

Use this information to help you decide whether or not you need more information about the entities mentioned in the report. You may also use your general knowledge to think of entities which may help enrich your answer.

You will also provide a full answer from the content you have available. Use the data provided to generate follow-up queries to help refine your search. Do not ask compound questions, for example: "What is the market cap of Apple and Microsoft?". Use your knowledge of the entity distribution to focus on entity types that will be useful for searching a broad area of the knowledge graph.

For the query:

{query}

The top-ranked community summaries:

{community_reports}

Provide the intermediate answer, and all scores in JSON format following:

{{'intermediate_answer': str,
'score': int,
'follow_up_queries': List[str]}}

Begin:
"""
