# Query Engine  🔎

The Query Engine is the retrieval module of the Graph RAG Library. It is one of the two main components of the Graph RAG library, the other being the Indexing Pipeline (see [Indexing Pipeline](../index/overview.md)).
It is responsible for the following tasks:

- [Local Search](#local-search)
- [Global Search](#global-search)
- [Question Generation](#question-generation)

## Local Search

Local search method generates answers by combining relevant data from the AI-extracted knowledge-graph with text chunks of the raw documents. This method is suitable for questions that require an understanding of specific entities mentioned in the documents (e.g. What are the healing properties of chamomile?).

For more details about how Local Search works please refer to the [Local Search](local_search.md) documentation.

## Global Search

Global search method generates answers by searching over all AI-generated community reports in a map-reduce fashion. This is a resource-intensive method, but often gives good responses for questions that require an understanding of the dataset as a whole (e.g. What are the most significant values of the herbs mentioned in this notebook?).

More about this can be checked at the [Global Search](global_search.md) documentation.

## Question Generation

This functionality takes a list of user queries and generates the next candidate questions. This is useful for generating follow-up questions in a conversation or for generating a list of questions for the investigator to dive deeper into the dataset.

Information about how question generation works can be found at the [Question Generation](question_generation.md) documentation page.
