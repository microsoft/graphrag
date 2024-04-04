# GraphRAG: Responsible AI FAQ 

## What is GraphRAG? 

GraphRAG is an AI-based content interpretation and search capability. Using LLMs, it parses data to create a knowledge graph and answer user questions about this private dataset.  GraphRAG works similarly to other AI-oriented search services, such as Microsoft AI Search. 

## What can GraphRAG do?  

GraphRAG is able to connect information across large volumes of information and use these connections to answer questions that are difficult or impossible to answer using keyword and vector-based search mechanisms Building on the previous question, provide semi-technical, high-level information on how the system offers functionality for various uses.  This lets a system using GraphRAG to answer questions where the answers span many documents as well as thematic questions such as “what are the top concerns in this dataset?.” 

## What are GraphRAG’s intended use(s)? 

GraphRAG is intended to support critical information discovery and analysis use cases where the information required to arrive at a useful insight spans many documents, is noisy, is mixed with mis and/or dis-information, or when the questions users aim to answer are more abstract or thematic than the underlying data can directly answer. 

GraphRAG is designed to be used in settings where users are already trained on responsible analytic approaches and critical reasoning is expected.  GraphRAG is capable of providing high degrees of insight on difficult information topics however it is not a technical panacea to problems where no single answer may exist. 

How was GraphRAG evaluated? What metrics are used to measure performance? 

GraphRAG has been evaluated in multiple ways.  The primary concerns are 1) accurate representation of the data set, 2) resilience to noise, misinformation, and disinformation, 3) providing transparency and provenance of information, 4) resilience to prompt and data corpus injection attacks, and 5) low hallucination rates.  Details on how each of these has been evaluated is outlined below by number. 

1) Accurate representation of the dataset has been tested by both manual inspection and automated testing against a “gold answer” that is created from randomly selected subsets of a test corpus. 

2) GraphRAG has been tested against datasets with known confusors and noise in multiple domains. These tests include both automated evaluation of answer detail (as compared to vector search approaches) as well as manual inspection using questions that are known to be difficult or impossible for other search systems to answer. 

3) Transparency and provenance is tested via automated answer coverage evaluation and human inspection of the underlying context returned. Additionally, adversarial testing is conducted using manually created test data specifically prepared to be difficult to detect. 

4) We test both user prompt injection attacks (“jailbreaks”) and cross prompt injection attacks (“data attacks”) using manual and semi-automated techniques. 

5) Hallucination rates are evaluated using claim coverage metrics, manual inspection of answer and source, and adversarial attacks to attempt a forced hallucination through adversarial and exceptionally challenging datasets. 

## What are the limitations of GraphRAG? How can users minimize the impact of GraphRAG’s limitations when using the system? 

GraphRAG depends on a well-constructed indexing examples.  For general applications (e.g. content oriented around people, places, organizations, things, etc.) we provide example indexing prompts. For unique datasets effective indexing can depend on proper identification of domain-specific concepts.   

Indexing is a relatively expensive operation; a best practice is to mitigate indexing is to create a small test dataset in the target domain to ensure indexer performance prior to large indexing operations. 

## What operational factors and settings allow for effective and responsible use of GraphRAG? 

GraphRAG is designed for use by users with domain sophistication and experience working through difficult information challenges.  While the approach is generally robust to injection attacks and identifying conflicting sources of information, the system is designed for trusted users.  Users that are trying to force an outcome may be able to find information that rationalizes a pre-determined answer.  Proper use of analytic tradecraft is important to generate reliable insights, and the provenance of information should be traced to ensure human agreement with the inferences made as part of the answer generation. 