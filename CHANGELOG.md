# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

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
