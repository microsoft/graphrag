# Indexing, Querying, and Prompt Tuning in GraphRAG for .NET

GraphRAG for .NET keeps feature parity with the Python reference project described in the [Microsoft Research blog](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/) and the [GraphRAG paper](https://arxiv.org/pdf/2404.16130). This document explains how the .NET workflows map to the concepts documented on [microsoft.github.io/graphrag](https://microsoft.github.io/graphrag/), highlights the supported query modes, and shows how to customise prompts via manual or auto tuning outputs.

## Indexing Architecture

- **Workflow parity.** Each indexing stage matches the Python pipeline and the [default data flow](https://microsoft.github.io/graphrag/index/default_dataflow/):
  - `load_input_documents` → `create_base_text_units` → `summarize_descriptions`
  - `extract_graph` persists `entities` and `relationships`
  - `create_communities` produces `communities`
  - `community_summaries` writes `community_reports`
  - `extract_covariates` stores `covariates`
- **Storage schema.** Tables share the column layout described under [index outputs](https://microsoft.github.io/graphrag/index/outputs/). The new strongly-typed records (`CommunityRecord`, `CovariateRecord`, etc.) mirror the JSON representation used by the Python implementation.
- **Cluster configuration.** `GraphRagConfig.ClusterGraph` exposes the same knobs as the Python `cluster_graph` settings, enabling largest-component filtering and deterministic seeding.

## Query Capabilities

The query layer ports the orchestrators documented in the [GraphRAG query overview](https://microsoft.github.io/graphrag/query/overview/):

- **Global search** ([docs](https://microsoft.github.io/graphrag/query/global_search/)) traverses community summaries and graph context to craft answers spanning the corpus.
- **Local search** ([docs](https://microsoft.github.io/graphrag/query/local_search/)) anchors on a document neighbourhood when you need focused context.
- **Drift search** ([docs](https://microsoft.github.io/graphrag/query/drift_search/)) monitors narrative changes across time slices.
- **Question generation** ([docs](https://microsoft.github.io/graphrag/query/question_generation/)) produces follow-up questions to extend an investigation.

Every orchestrator consumes the same indexed tables as the Python project, so the .NET stack interoperates with BYOG scenarios described in the [index architecture guide](https://microsoft.github.io/graphrag/index/architecture/).

## Prompt Tuning

Manual and auto prompt tuning are both available without code changes:

1. **Manual overrides** follow the rules from [manual prompt tuning](https://microsoft.github.io/graphrag/prompt_tuning/manual_prompt_tuning/).
   - Place custom templates under a directory referenced by `GraphRagConfig.PromptTuning.Manual.Directory` and set `Enabled = true`.
   - Filenames follow the stage key pattern `section/workflow/kind.txt` (see table below).
2. **Auto tuning** integrates the outputs documented in [auto prompt tuning](https://microsoft.github.io/graphrag/prompt_tuning/auto_prompt_tuning/).
   - Point `GraphRagConfig.PromptTuning.Auto.Directory` at the folder containing the generated prompts and set `Enabled = true`.
   - The runtime prefers explicit paths from workflow configs, then manual overrides, then auto-tuned files, and finally the built-in defaults in `prompts/`.

### Stage Keys and Placeholders

| Workflow | Stage key | Purpose | Supported placeholders |
|----------|-----------|---------|------------------------|
| `extract_graph` (system) | `index/extract_graph/system.txt` | System prompt that instructs the extractor. | _N/A_ |
| `extract_graph` (user) | `index/extract_graph/user.txt` | User prompt template for individual text units. | `{{max_entities}}`, `{{text}}` |
| `community_summaries` (system) | `index/community_reports/system.txt` | System guidance for cluster summarisation. | _N/A_ |
| `community_summaries` (user) | `index/community_reports/user.txt` | User prompt template for entity lists. | `{{max_length}}`, `{{entities}}` |

Placeholders are replaced at runtime with values drawn from workflow configuration:

- `{{max_entities}}` → `ExtractGraphConfig.EntityTypes.Count + 5` (minimum 1)
- `{{text}}` → the original text unit content
- `{{max_length}}` → `CommunityReportsConfig.MaxLength`
- `{{entities}}` → bullet list of entity titles and descriptions

If a template is omitted, the runtime falls back to the built-in prompts stored under `prompts/` and bundled with the repository.

## Integration Tests

`tests/ManagedCode.GraphRag.Tests/Integration/CommunitySummariesIntegrationTests.cs` exercises the new prompt loader end-to-end using the file-backed pipeline storage. Combined with the existing Aspire-powered suites, the tests demonstrate how indexing, community detection, and summarisation behave with tuned prompts while remaining faithful to the [GraphRAG BYOG guidance](https://microsoft.github.io/graphrag/index/byog/).

## Further Reading

- [GraphRAG prompt tuning overview](https://microsoft.github.io/graphrag/prompt_tuning/overview/)
- [GraphRAG index methods](https://microsoft.github.io/graphrag/index/methods/)
- [GraphRAG query overview](https://microsoft.github.io/graphrag/query/overview/)
- [GraphRAG default dataflow](https://microsoft.github.io/graphrag/index/default_dataflow/)

These resources underpin the .NET implementation and provide broader context for customising or extending the library.
