# GraphRAG .NET Porting Plan

This working note documents the mapping between the Python implementation that lives in `submodules/graphrag-python` and the forthcoming .NET port.  It exists purely as a checklist for the migration effort and will be removed once parity has been achieved.

## High-Level Architecture

- **Configuration** – `GraphRagConfig` and companion models will be introduced under `GraphRag.Config`.  They mirror the Pydantic models (`graphrag.config.models`) and keep JSON/YAML compatibility with the original schema.
- **Indexing Pipeline** – `GraphRag.Indexing` now ships `PipelineExecutor`, `IndexingPipelineRunner`, and translated workflows (`load_input_documents`, `create_base_text_units`, `create_final_documents`) with tokenization powered by `Microsoft.ML.Tokenizers`. Text ingestion supports text/CSV/JSON sources with the same grouping semantics as Python.
- **Query Pipeline** – `GraphRag.Query` mirrors `graphrag.query.*` with orchestrators for question generation, context assembly, and answer synthesis.
- **Storage** – `GraphRag.Storage` offers a provider model equivalent to `PipelineStorage` (file, memory, Blob, Cosmos).  A JSON-backed table serializer is in place while the Parquet implementation is ported.
- **Graph Stores** – Postgres adapter issues parameterised Cypher queries (AGE) to avoid injection; unit tests assert payload sanitisation.
- **Language Models & Tokenizers** – `GraphRag.LanguageModel` wraps Azure OpenAI/LiteLLM equivalents.  Configuration, retry, and rate limiting concepts are ported.
- **Vector Stores** – `GraphRag.VectorStores` brings adapters for local FAISS-like embeddings, Azure Cognitive Search, and Postgres pgvector matching the Python `vector_stores`.
- **Callbacks & Telemetry** – `GraphRag.Callbacks` contains workflow lifecycle hooks, tracing, and instrumentation mirroring `WorkflowCallbacks`.

## Data Model Mapping

| Python Table | Python Module | .NET Type | Notes |
|--------------|---------------|-----------|-------|
| `documents` | `index/workflows/create_final_documents.py` | `DocumentRecord` | Stored as Parquet; includes metadata dictionary. |
| `text_units` | `index/workflows/create_base_text_units.py` | `TextUnitRecord` | Chunk metadata + document ids. |
| `entities` | `index/workflows/extract_graph.py` | `EntityRecord` | Already partially ported; will be extended with raw view support. |
| `relationships` | `index/workflows/extract_graph.py` | `RelationshipRecord` | Already present; to be aligned with Python schema. |
| `communities` | `index/workflows/create_communities.py` | `CommunityRecord` | Requires Louvain modularity implementation. |
| `community_reports` | `index/workflows/create_community_reports.py` | `CommunityReportRecord` | Needs summarization prompts and structured output. |
| `covariates` | `index/workflows/extract_covariates.py` | `CovariateRecord` | Includes temporal fields, subject/object ids. |

## Testing Strategy

- Translate Python unit/integration suites under `submodules/graphrag-python/tests`.
- Use xUnit with Aspire-powered fixtures (Neo4j, Postgres, Cosmos emulator) to run end-to-end indexing + query scenarios.
- For LLM-dependent steps, rely on configurable providers with live credentials; tests skip only when mandatory environment variables are absent.
- Golden datasets from `tests/fixtures` are copied into `.NET` test resources to validate data transformations.

## Immediate TODOs

1. Implement configuration model layer (`GraphRag.Config`). ✅
2. Port pipeline runtime (`GraphRag.Indexing.Runtime`) including callback chain, run loop, benchmarking. ✅
3. Recreate storage adapters (File, Memory) and Parquet serializer (JSON stub ready, Parquet pending).
4. Translate remaining workflows beyond ingestion (graph extraction, summarisation, embeddings).
5. Migrate vector store + embedding interfaces and integrate into indexing pipeline.
6. Recreate query orchestrator and evaluation pipelines.
7. Grow the .NET test suite (unit + integration) to ~85 % coverage and parity with Python scenarios.

> This file is intentionally temporary; it guides the phased port while the codebase is in flux.
