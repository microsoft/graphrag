# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 2.2.1

- patch: Fix Community Report prompt tuning response
- patch: Fix graph creation missing edge weights.
- patch: Update as workflows

## 2.2.0

- minor: Support OpenAI reasoning models.
- patch: Add option to snapshot raw extracted graph tables.
- patch: Added batching logic to the prompt tuning autoselection embeddings workflow
- patch: Align config classes and docs better.
- patch: Align embeddings table loading with configured fields.
- patch: Brings parity with our latest NLP extraction approaches.
- patch: Fix fnllm to 0.2.3
- patch: Fixes to basic search.
- patch: Update llm args for consistency.
- patch: add vector store integration tests

## 2.1.0

- minor: Add support for JSON input files.
- minor: Updated the prompt tunning client to support csv-metadata injection and updated output file types to match the new naming convention.
- patch: Add check for custom model types while config loading
- patch: Adds general-purpose pipeline run state object.

## 2.0.0

- major: Add children to communities to avoid re-compute.
- major: Reorganize and rename workflows and their outputs.
- major: Rework API to accept callbacks.
- minor: Add LMM Manager and Factory, to support provider registration
- minor: Add NLP graph extraction.
- minor: Add pipeline_start and pipeline_end callbacks.
- minor: Move embeddings snapshots to the workflow runner.
- minor: Remove config inheritance, hydration, and automatic env var overlays.
- minor: Rework the update output storage structure.
- patch: Add caching to NLP extractor.
- patch: Add vector store id reference to embeddings config.
- patch: Export NLP community reports prompt.
- patch: Fix DRIFT search on Azure AI Search.
- patch: Fix StopAsyncIteration catch.
- patch: Fix missing embeddings workflow in FastGraphRAG.
- patch: Fix proper use of n_depth for drift search
- patch: Fix report generation recursion.
- patch: Fix summarization over large datasets for inc indexing. Fix relationship summarization
- patch: Optimize data iteration by removing some iterrows from code
- patch: Patch json mode for community reports
- patch: Properly increment text unit IDs during updates.
- patch: Refactor config defaults from constants to type-safe, hierarchical dataclass.
- patch: Require explicit azure auth settings when using AOI.
- patch: Separates graph pruning for differential usage.
- patch: Tuck flow functions under their workflow modules.
- patch: Update fnllm. Remove unused libs.
- patch: Use ModelProvider for query module
- patch: Use shared schema for final outputs.
- patch: add dynamic retry logic.
- patch: add option to prepend metadata into chunks
- patch: cleanup query code duplication.
- patch: implemented multi-index querying for api layer
- patch: multi index query cli support
- patch: remove unused columns and change property document_attribute_columns to metadata
- patch: update multi-index query to support new workflows

## 1.2.0

- minor: Add Drift Reduce response and streaming endpoint
- minor: add cosmosdb vector store
- patch: Fix example notebooks
- patch: Set default rate limits.
- patch: unit tests for text_splitting

## 1.2.0

- patch: Basic Rag minor fix

## 1.1.1

- patch: Fix a bug on creating community hierarchy for dynamic search
- patch: Increase LOCAL_SEARCH_COMMUNITY_PROP to 15%

## 1.1.0

- minor: Make gleanings independent of encoding
- minor: Remove DataShaper (first steps).
- minor: Remove old pipeline runner.
- minor: new search implemented as a new option for the api
- patch: Fix gleanings loop check
- patch: Implement cosmosdb storage option for cache and output
- patch: Move extractor code to co-locate with operations.
- patch: Remove config input models.
- patch: Ruff update
- patch: Simplify and streamline internal config.
- patch: Simplify callbacks model.
- patch: Streamline flows.
- patch: fix instantiation of storage classes.

## 1.0.1

- patch: Fix encoding model config parsing
- patch: Fix exception on error callbacks
- patch: Manage llm instances inside a cached singleton. Check for empty dfs after entity/relationship extraction
- patch: Respect encoding_model option

## 1.0.0

- patch: Add Parent id to communities data model
- patch: Add migration notebook.
- patch: Create separate community workflow, collapse subflows.
- patch: Dependency Updates
- patch: cleanup and refactor factory classes.

## 0.9.0

- minor: Refactor graph creation.
- patch: Dependency updates
- patch: Fix Global Search with dynamic Community selection bug
- patch: Fix question gen.
- patch: Optimize Final Community Reports calculation and stabilize cache
- patch: miscellaneous code cleanup and minor changes for better alignment of style across the codebase.
- patch: replace llm package with fnllm
- patch: replaced md5 hash with sha256
- patch: replaced md5 hash with sha512
- patch: update API and add a demonstration notebook

## 0.5.0

- minor: Data model changes.
- patch: Add Parquet as part of the default emitters when not pressent
- patch: Centralized prompts and export all for easier injection.
- patch: Cleanup of artifact outputs/schemas.
- patch: Config and docs updates.
- patch: Implement dynamic community selection to global search
- patch: fix autocompletion of existing files/directory paths.
- patch: move import statements out of init files

## 0.4.1

- patch: Add update cli entrypoint for incremental indexing
- patch: Allow some CI/CD jobs to skip PRs dedicated to doc updates only.
- patch: Fix a file paths issue in the viz guide.
- patch: Fix optional covariates update in incremental indexing
- patch: Raise error on empty deltas for inc indexing
- patch: add visualization guide to doc site
- patch: fix streaming output error

## 0.4.0

- minor: Add Incremental Indexing
- minor: Added DRIFT graph reasoning query module
- minor: embeddings moved to a different workflow
- patch: Add DRIFT search cli and example notebook
- patch: Add config for incremental updates
- patch: Add embeddings to subflow.
- patch: Add naive community merge using time period
- patch: Add relationship merge
- patch: Add runtime-only storage option.
- patch: Add text units update
- patch: Allow empty workflow returns to avoid disk writing.
- patch: Apply pandas optimizations to create final entities
- patch: Calculate new inputs and deleted inputs on update
- patch: Collapse covariates flow.
- patch: Collapse create-base-entity-graph.
- patch: Collapse create-final-community-reports.
- patch: Collapse create-final-documents.
- patch: Collapse create-final-entities.
- patch: Collapse create-final-nodes.
- patch: Collapse create_base_documents.
- patch: Collapse create_base_text_units.
- patch: Collapse create_final_relationships.
- patch: Collapse entity extraction.
- patch: Collapse entity summarize.
- patch: Collapse intermediate workflow outputs.
- patch: Dependency updates
- patch: Extract DataShaper-less flows.
- patch: Fix Community ID loading for DRIFT search over existing indexes
- patch: Fix embeddings faulty assignments
- patch: Fix init defaults for vector store and drift img in docs
- patch: Fix nested json parsing
- patch: Fix some edge cases on Drift Search over small input sets
- patch: Fix var name for embedding
- patch: Merge existing and new entities, updating values accordingly
- patch: Merge text_embed into create-final-relationships subflow.
- patch: Move embedding verbs to operations.
- patch: Moving verbs around.
- patch: Optimize Create Base Documents subflow
- patch: Optimize text unit relationship count
- patch: Perf optimizations in map_query_to_entities()
- patch: Remove aggregate_df from final coomunities and final text units
- patch: Remove duplicated relationships and nodes
- patch: Remove unused column from final entities
- patch: Reorganized api,reporter,callback code into separate components. Defined debug profiles.
- patch: Small cleanup in community context history building
- patch: Transient entity graph and snapshotting.
- patch: Update Incremental Indexing to new embeddings workflow
- patch: Use mkdocs for documentation
- patch: add backwards compatibility patch to vector store.
- patch: add-autogenerated-cli-docs
- patch: fix docs image path
- patch: refactor use of vector stores and update support for managed identity
- patch: remove redundant error-handling code from global-search
- patch: reorganize cli layer

## 0.3.6

- patch: Collapse create_final_relationships.
- patch: Dependency update and cleanup

## 0.3.5

- patch: Add compound verbs with tests infra.
- patch: Collapse create_final_communities.
- patch: Collapse create_final_text_units.
- patch: Covariate verb collapse.
- patch: Fix duplicates in community context builder
- patch: Fix prompt tune output path
- patch: Fix seed hardcoded init
- patch: Fix seeded random gen on clustering
- patch: Improve logging.
- patch: Set default values for cli parameters.
- patch: Use static output directories.

## 0.3.4

- patch: Deep copy txt units on local search to avoid race conditions
- patch: Fix summarization including empty descriptions

## 0.3.3

- patch: Add entrypoints for incremental indexing
- patch: Clean up and organize run index code
- patch: Consistent config loading. Resolves #99 and Resolves #1049
- patch: Fix circular dependency when running prompt tune api directly
- patch: Fix default settings for embedding
- patch: Fix img for auto tune
- patch: Fix img width
- patch: Fixed a bug in prompt tuning process
- patch: Refactor text unit build at local search
- patch: Update Prompt Tuning docs
- patch: Update create_pipeline_config.py
- patch: Update prompt tune command in docs
- patch: add querying from azure blob storage
- patch: fix setting base_dir to full paths when not using file system.
- patch: fix strategy config in entity_extraction

## 0.3.2

- patch: Add context data to query API responses.
- patch: Add missing config parameter documentation for prompt tuning
- patch: Add neo4j community notebook
- patch: Ensure entity types to be str when running prompt tuning
- patch: Fix weight casting during graph extraction
- patch: Patch "past" dependency issues
- patch: Update developer guide.
- patch: Update query type hints.
- patch: change-lancedb-placement

## 0.3.1

- patch: Add preflight check to check LLM connectivity.
- patch: Add streaming support for local/global search to query cli
- patch: Add support for both float and int on schema validation for community report generation
- patch: Avoid running index on gh-pages publishing
- patch: Implement Index API
- patch: Improves filtering for data dir inferring
- patch: Update to nltk 3.9.1

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
