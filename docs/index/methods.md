# Indexing Methods

GraphRAG is a platform for our research into RAG indexing methods that produce optimal context window content for language models. We have a standard indexing pipeline that uses a language model to extract the graph that our memory model is based upon. We may introduce additional indexing methods from time to time. This page documents those options.

## Standard GraphRAG

This is the method described in the original [blog post](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/). Standard uses a language model for all reasoning tasks:

- entity extraction: LLM is prompted to extract named entities and provide a description from each text unit.
- relationship extraction: LLM is prompted to describe the relationship between each pair of entities in each text unit.
- entity summarization: LLM is prompted to combine the descriptions for every instance of an entity found across the text units into a single summary.
- relationship summarization: LLM is prompted to combine the descriptions for every instance of a relationship found across the text units into a single summary.
- claim extraction (optiona): LLM is prompted to extract and describe claims from each text unit.
- community report generation: entity and relationship descriptions (and optionally claims) for each community are collected and used to prompt the LLM to generate a summary report.

`graphrag index --method standard`. This is the default method, so the method param can actual be omitted.

## FastGraphRAG

FastGraphRAG is a method that substitutes some of the language model reasoning for traditional natural language processing (NLP) methods. This is a hybrid technique that we developed as a faster and cheaper indexing alternative:

- entity extraction: entities are noun phrases extracted using NLP libraries such as NLTK and spaCy. There is no description; the source text unit is used for this.
- relationship extraction: relationships are defined as text unit co-occurrence between entity pairs. There is no description.
- entity summarization: not necessary.
- relationship summarization: not necessary.
- claim extraction (optiona): unused.
- community report generation: The direct text unit content containing each entity noun phrase is collected and used to prompt the LLM to generate a summary report.

`graphrag index --method fast`

FastGraphRAG has a handful of NLP [options built in](https://microsoft.github.io/graphrag/config/yaml/#extract_graph_nlp). By default we use NLTK + regular expressions for the noun phrase extraction, which is very fast but primarily suitable for English. We have built in two additional methods using spaCy: semantic parsing and CFG. We use the `en_core_web_md` model by default for spaCy, but note that you can reference any [supported model](https://spacy.io/models/) that you have installed. 

Note that we also generally configure the text chunking to produce much smaller chunks (50-100 tokens). This results in a better co-occurrence graph.

⚠️ Note on SpaCy models:

This package requires SpaCy models to function correctly. If the required model is not installed, the package will automatically download and install it the first time it is used.

You can install it manually by running `python -m spacy download <model_name>`, for example `python -m spacy download en_core_web_md`.


## Choosing a Method

Standard GraphRAG provides a rich description of real-world entities and relationships, but is more expensive that FastGraphRAG. We estimate graph extraction to constitute roughly 75% of indexing cost. FastGraphRAG is therefore much cheaper, but the tradeoff is that the extracted graph is less directly relevant for use outside of GraphRAG, and the graph tends to be quite a bit noisier. If high fidelity entities and graph exploration are important to your use case, we recommend staying with traditional GraphRAG. If your use case is primarily aimed at summary questions using global search, FastGraphRAG is a reasonable and cheaper alternative.
