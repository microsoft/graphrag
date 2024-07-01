# GraphRAG: Responsible AI FAQ 

## What is GraphRAG? 

GraphRAG is an AI-based content interpretation and search capability. Using LLMs, it parses data to create a knowledge graph and answer user questions about a user-provided private dataset. 

## What can GraphRAG do?  

GraphRAG is able to connect information across large volumes of information and use these connections to answer questions that are difficult or impossible to answer using keyword and vector-based search mechanisms. Building on the previous question, provide semi-technical, high-level information on how the system offers functionality for various uses.  This lets a system using GraphRAG to answer questions where the answers span many documents as well as thematic questions such as “what are the top themes in this dataset?.”

## What are GraphRAG’s intended use(s)? 

* GraphRAG is intended to support critical information discovery and analysis use cases where the information required to arrive at a useful insight spans many documents, is noisy, is mixed with mis and/or dis-information, or when the questions users aim to answer are more abstract or thematic than the underlying data can directly answer. 
* GraphRAG is designed to be used in settings where users are already trained on responsible analytic approaches and critical reasoning is expected. GraphRAG is capable of providing high degrees of insight on complex information topics, however human analysis by a domain expert of the answers is needed in order to verify and augment GraphRAG’s generated responses. 
* GraphRAG is intended to be deployed and used with a domain specific corpus of text data. GraphRAG itself does not collect user data, but users are encouraged to verify data privacy policies of the chosen LLM used to configure GraphRAG. 

## How was GraphRAG evaluated? What metrics are used to measure performance? 

GraphRAG has been evaluated in multiple ways.  The primary concerns are 1) accurate representation of the data set, 2) providing transparency and  groundedness of responses, 3) resilience to prompt and data corpus injection attacks, and 4) low hallucination rates.  Details on how each of these has been evaluated is outlined below by number. 

1) Accurate representation of the dataset has been tested by both manual inspection and automated testing against a “gold answer” that is created from randomly selected subsets of a test corpus. 

2) Transparency and groundedness of responses is tested via automated answer coverage evaluation and human inspection of the underlying context returned.  

3) We test both user prompt injection attacks (“jailbreaks”) and cross prompt injection attacks (“data attacks”) using manual and semi-automated techniques. 

4) Hallucination rates are evaluated using claim coverage metrics, manual inspection of answer and source, and adversarial attacks to attempt a forced hallucination through adversarial and exceptionally challenging datasets. 

## What are the limitations of GraphRAG? How can users minimize the impact of GraphRAG’s limitations when using the system? 

GraphRAG depends on a well-constructed indexing examples.  For general applications (e.g. content oriented around people, places, organizations, things, etc.) we provide example indexing prompts. For unique datasets effective indexing can depend on proper identification of domain-specific concepts.   

Indexing is a relatively expensive operation; a best practice to mitigate indexing is to create a small test dataset in the target domain to ensure indexer performance prior to large indexing operations. 

## What operational factors and settings allow for effective and responsible use of GraphRAG? 

GraphRAG is designed for use by users with domain sophistication and experience working through difficult information challenges.  While the approach is generally robust to injection attacks and identifying conflicting sources of information, the system is designed for trusted users. Proper human analysis of responses is important to generate reliable insights, and the provenance of information should be traced to ensure human agreement with the inferences made as part of the answer generation. 

GraphRAG yields the most effective results on natural language text data that is collectively focused on an overall topic or theme, and that is entity rich – entities being people, places, things, or objects that can be uniquely identified. 

While GraphRAG has been evaluated for its resilience to prompt and data corpus injection attacks, and has been probed for specific types of harms, the LLM that the user configures with GraphRAG may produce inappropriate or offensive content, which may make it inappropriate to deploy for sensitive contexts without additional mitigations that are specific to the use case and model. Developers should assess outputs for their context and use available safety classifiers, model specific safety filters and features (such as https://azure.microsoft.com/en-us/products/ai-services/ai-content-safety), or custom solutions appropriate for their use case. 