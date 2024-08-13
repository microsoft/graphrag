# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 0.3.0

- minor: Implement auto templating API.
- minor: Implement query engine API.
- patch: Fix file dumps using json for non ASCII chars
- patch: Stabilize smoke tests for query context building
- patch: fix query embedding
- patch: fix sort_context & max_tokens params in verb

## 0.2.2

- patch: Add a check if there is no community record added in local search context
- patch: Add sepparate workflow for Python Tests
- patch: Docs updates
- patch: Run smoke tests on 4o

## 0.2.1

- patch: Added default columns for vector store at create_pipeline_config. No change for other cases.
- patch: Change json parsing error in the map step of global search to warning
- patch: Fix Local Search breaking when loading Embeddings input. Defaulting overwrite to True as in the rest of the vector store config
- patch: Fix json parsing when LLM returns faulty responses
- patch: Fix missing community reports and refactor community context builder
- patch: Fixed a bug that erased the vector database, added a new parameter to specify the config file path, and updated the documentation accordingly.
- patch: Try parsing json before even repairing
- patch: Update Prompt Tuning meta prompts with finer examples
- patch: Update default entity extraction and gleaning prompts to reduce hallucinations
- patch: add encoding-model to entity/claim extraction config
- patch: add encoding-model to text chunking config
- patch: add user prompt to history-tracking llm
- patch: update config reader to allow for zero gleans
- patch: update config-reader to allow for empty chunk-by arrays
- patch: update history-tracking LLm to use 'assistant' instead of 'system' in output history.
- patch: use history argument in hash key computation; add history input to cache data

## 0.2.0

- minor: Add content-based KNN for selecting prompt tune few shot examples
- minor: Add dynamic community report rating to the prompt tuning engine
- patch: Add Minute-based Rate Limiting and fix rpm, tpm settings
- patch: Add N parameter support
- patch: Add cli flag to overlay default values onto a provided config.
- patch: Add exception handling on file load
- patch: Add language support to prompt tuning
- patch: Add llm params to local and global search
- patch: Fix broken prompt tuning link on docs
- patch: Fix delta none on query calls
- patch: Fix docsite base url
- patch: Fix encoding model parameter on prompt tune
- patch: Fix for --limit exceeding the dataframe length
- patch: Fix for Ruff 0.5.2
- patch: Fixed an issue where base OpenAI embeddings can't work with Azure OpenAI LLM
- patch: Modify defaults for CHUNK_SIZE, CHUNK_OVERLAP and GLEANINGS to reduce time and LLM calls
- patch: fix community_report doesn't work in settings.yaml
- patch: fix llm response content is None in query
- patch: fix the organization parameter is ineffective during queries
- patch: remove duplicate file read
- patch: support non-open ai model config to prompt tune
- patch: use binary io processing for all file io operations

## 0.1.0

- minor: Initial Release
