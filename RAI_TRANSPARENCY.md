# GraphRAG: Responsible AI FAQ

## What is GraphRAG?

GraphRAG is an AI-based content interpretation and search capability. Using LLMs, it parses data to create a knowledge graph and answer user questions about a user-provided private dataset.

## What can GraphRAG do?

GraphRAG can connect information across large volumes of data and use these connections to answer questions that are difficult or impossible to answer using keyword- and vector-based search mechanisms. This enables a system using GraphRAG to answer questions whose answers span many documents, as well as thematic questions such as “What are the top themes in this dataset?”

## What are GraphRAG’s intended use(s)?

* GraphRAG is intended to support critical information discovery and analysis use cases where the information required to arrive at a useful insight spans many documents, is noisy, is mixed with misinformation or disinformation, or involves questions that are more abstract or thematic than the underlying data can directly answer.
* GraphRAG is designed for settings where users are trained in responsible analytic approaches and expected to apply critical reasoning. GraphRAG can provide deep insight into complex information topics; however, a domain expert should analyze its answers to verify and augment the generated responses.
* GraphRAG is intended to be deployed and used with a domain-specific corpus of text data. GraphRAG itself does not collect user data, but users are encouraged to verify the data privacy policies of the LLM used to configure GraphRAG.

## How was GraphRAG evaluated? What metrics are used to measure performance?

GraphRAG has been evaluated in multiple ways. The primary concerns are 1) accurate representation of the dataset, 2) transparency and groundedness of responses, 3) resilience to prompt and data corpus injection attacks, and 4) low hallucination rates. Details on how each concern was evaluated are outlined below.

1) Accurate representation of the dataset has been tested through both manual inspection and automated testing against a “gold answer” created from randomly selected subsets of a test corpus.

2) Transparency and groundedness of responses are tested through automated answer coverage evaluation and human inspection of the returned context.

3) We test both user prompt injection attacks (“jailbreaks”) and cross-prompt injection attacks (“data attacks”) using manual and semi-automated techniques.

4) Hallucination rates are evaluated using claim coverage metrics, manual inspection of answers and sources, and attempts to force hallucinations through adversarial and exceptionally challenging datasets.

## What are the limitations of GraphRAG? How can users minimize the impact of GraphRAG’s limitations when using the system?

GraphRAG depends on well-constructed indexing prompts. For general applications (for example, content about people, places, organizations, or things), we provide example prompts. For unique datasets, effective indexing can depend on properly identifying domain-specific concepts.

Indexing is a relatively expensive operation. To mitigate its cost, create a small test dataset in the target domain to evaluate indexer performance before running large indexing operations.

## What operational factors and settings allow for effective and responsible use of GraphRAG?

GraphRAG is designed for users with domain expertise and experience working through difficult information challenges. While the approach is generally robust to injection attacks and can identify conflicting sources of information, the system is designed for trusted users. Human analysis of responses is important for generating reliable insights, and information provenance should be traced to verify the inferences made during answer generation.

GraphRAG yields the most effective results on natural-language text data focused on an overall topic or theme and rich in identifiable entities such as people, places, or objects.

While GraphRAG has been evaluated for resilience to prompt and data corpus injection attacks and probed for specific types of harm, the configured LLM may produce inappropriate or offensive content. This may make GraphRAG unsuitable for sensitive contexts without additional mitigations specific to the use case and model. Developers should assess outputs for their context and use available safety classifiers, model-specific safety filters and features (such as [Azure AI Content Safety](https://azure.microsoft.com/en-us/products/ai-services/ai-content-safety)), or custom solutions appropriate for their use case.