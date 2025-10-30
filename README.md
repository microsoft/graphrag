# GraphRAG for .NET

GraphRAG for .NET is a ground-up port of Microsoft’s original GraphRAG Python reference implementation to the modern .NET 9 stack.  
Our goal is API parity with the Python pipeline while embracing native .NET idioms (dependency injection, logging abstractions, async I/O, etc.).  
The upstream Python code remains available in `submodules/graphrag-python` for side-by-side reference during the migration.

---

## Repository Structure

```
graphrag/
├── GraphRag.slnx                          # Single solution covering every project
├── Directory.Build.props / Directory.Packages.props
├── src/
│   ├── ManagedCode.GraphRag               # Core pipeline orchestration & abstractions
│   ├── ManagedCode.GraphRag.CosmosDb      # Azure Cosmos DB graph adapter
│   ├── ManagedCode.GraphRag.Neo4j         # Neo4j adapter & bolt client integration
│   └── ManagedCode.GraphRag.Postgres      # Apache AGE/PostgreSQL graph store adapter
├── tests/
│   └── ManagedCode.GraphRag.Tests
│       ├── Integration/                   # Live container-backed scenarios (Testcontainers)
│       └── … unit-level suites
└── submodules/
    └── graphrag-python                    # Original Python implementation (read-only reference)
```

### Key Components

- **ManagedCode.GraphRag**  
  Hosts the pipelines, workflow execution model, and shared contracts such as `IGraphStore`, `IPipelineCache`, etc.

- **ManagedCode.GraphRag.Neo4j / .Postgres / .CosmosDb**  
  Concrete graph-store adapters that satisfy the core abstractions. Each hides the backend-specific SDK plumbing and exposes `.AddXGraphStore(...)` DI helpers.

- **ManagedCode.GraphRag.Tests**  
  Our only test project.  
  Unit tests ensure helper APIs behave deterministically.  
  The `Integration/` folder spins up real infrastructure (Neo4j, Apache AGE/PostgreSQL, optional Cosmos) via Testcontainers—no fakes or mocks.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| [.NET SDK 9.0](https://dotnet.microsoft.com/en-us/download/dotnet/9.0) | The solution targets `net9.0`; install previews where necessary. |
| Docker Desktop / compatible container runtime | Required for Testcontainers-backed integration tests (Neo4j & Apache AGE/PostgreSQL). |
| (Optional) Azure Cosmos DB Emulator | Set `COSMOS_EMULATOR_CONNECTION_STRING` to enable Cosmos tests; they are skipped when the env var is absent. |

---

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-org>/graphrag.git
   cd graphrag
   git submodule update --init --recursive
   ```

2. **Restore & build**
   ```bash
   dotnet build GraphRag.slnx
   ```
   > Repository rule: always build the solution before running tests.

3. **Run the full test suite**
   ```bash
   dotnet test GraphRag.slnx --logger "console;verbosity=minimal"
   ```
   This command will:
   - Restore packages
   - Launch Neo4j and Apache AGE/PostgreSQL containers via Testcontainers
   - Execute unit + integration tests from `ManagedCode.GraphRag.Tests`
   - Tear down containers automatically when finished

4. **Limit to a specific integration area (optional)**
   ```bash
   dotnet test tests/ManagedCode.GraphRag.Tests/ManagedCode.GraphRag.Tests.csproj \
       --filter "FullyQualifiedName~PostgresGraphStoreIntegrationTests" \
       --logger "console;verbosity=normal"
   ```

---

## Integration Testing Strategy

- **No fakes.** We removed the legacy fake Postgres store. Every graph operation in tests uses real services orchestrated by Testcontainers.
- **Security coverage.** `Integration/PostgresGraphStoreIntegrationTests.cs` includes payloads that mimic SQL/Cypher injection attempts to ensure values remain literals and labels/types are strictly validated.
- **Cross-backend validation.** `Integration/GraphStoreIntegrationTests.cs` exercises Postgres, Neo4j, and Cosmos (when available) through the shared `IGraphStore` abstraction.
- **Workflow smoke tests.** Pipelines (e.g., `IndexingPipelineRunnerTests`) and finalization steps run end-to-end with the fixture-provisioned infrastructure.
- **Prompt precedence.** `Integration/CommunitySummariesIntegrationTests.cs` proves manual prompt overrides win over auto-tuned assets while still falling back to auto templates when manual text is absent.
- **Callback and stats instrumentation.** `Runtime/PipelineExecutorTests.cs` now asserts that pipeline callbacks fire and runtime statistics are captured even when workflows fail early, so custom telemetry remains reliable.

---

## Pipeline Cache

Pipelines exchange state through the `IPipelineCache` abstraction. Every workflow step receives the same cache instance via `PipelineRunContext`, so it can reuse expensive results (LLM calls, chunk expansions, graph lookups) that were produced earlier in the run instead of recomputing them. The cache also keeps optional debug payloads per entry so you can persist trace metadata alongside the main value.

To use the built-in in-memory cache, register it alongside the standard ASP.NET Core services:

```csharp
using GraphRag.Cache;

builder.Services.AddMemoryCache();
builder.Services.AddSingleton<IPipelineCache, MemoryPipelineCache>();
```

Prefer a different backend? Implement `IPipelineCache` yourself and register it through DI—the pipeline will pick up your custom cache automatically.

- **Per-scope isolation.** `MemoryPipelineCache.CreateChild("stage")` scopes keys by prefix (`parent:stage:key`). Calling `ClearAsync` on the parent removes every nested key, so multi-step workflows do not leak data between stages.
- **Debug traces.** The cache stores optional debug payloads per entry; `DeleteAsync` and `ClearAsync` always clear these traces, preventing the diagnostic dictionary from growing unbounded.
- **Lifecycle guidance.** Create the root cache once per pipeline run (the default context factory does this for you) and spawn children inside individual workflows when you need an isolated namespace.

---

## Language Model Registration

GraphRAG delegates language-model configuration to [Microsoft.Extensions.AI](https://learn.microsoft.com/dotnet/ai/overview). Register keyed clients for every `ModelId` you reference in configuration—pick any string key that matches your config:

```csharp
using Azure;
using Azure.AI.OpenAI;
using GraphRag.Config;
using Microsoft.Extensions.AI;

var openAi = new OpenAIClient(new Uri(endpoint), new AzureKeyCredential(key));
const string chatModelId = "chat_model";
const string embeddingModelId = "embedding_model";

builder.Services.AddKeyedSingleton<IChatClient>(
    chatModelId,
    _ => openAi.GetChatClient(chatDeployment));

builder.Services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding>>(
    embeddingModelId,
    _ => openAi.GetEmbeddingClient(embeddingDeployment));
```

Rate limits, retries, and other policies should be configured when you create these clients (for example by wrapping them with `Polly` handlers). `GraphRagConfig.Models` simply tracks the set of model keys that have been registered so overrides can validate references.

---

## Indexing, Querying, and Prompt Tuning Alignment

The .NET port mirrors the [GraphRAG indexing architecture](https://microsoft.github.io/graphrag/index/overview/) and its query workflows so downstream applications retain parity with the Python reference implementation.

- **Indexing overview.** Workflows such as `extract_graph`, `create_communities`, and `community_summaries` map 1:1 to the [default data flow](https://microsoft.github.io/graphrag/index/default_dataflow/) and persist the same tables (`text_units`, `entities`, `relationships`, `communities`, `community_reports`, `covariates`). The new prompt template loader honours manual or auto-tuned prompts before falling back to the stock templates in `prompts/`.
- **Query capabilities.** The query pipeline retains global search, local search, drift search, and question generation semantics described in the [GraphRAG query overview](https://microsoft.github.io/graphrag/query/overview/). Each orchestrator continues to assemble context from the indexed tables so you can reference [global](https://microsoft.github.io/graphrag/query/global_search/) or [local](https://microsoft.github.io/graphrag/query/local_search/) narratives interchangeably.
- **Prompt tuning.** GraphRAG’s [manual](https://microsoft.github.io/graphrag/prompt_tuning/manual_prompt_tuning/) and [auto](https://microsoft.github.io/graphrag/prompt_tuning/auto_prompt_tuning/) strategies are surfaced through `GraphRagConfig.PromptTuning`. Store custom templates under `prompts/` or point `PromptTuning.Manual.Directory`/`PromptTuning.Auto.Directory` at your tuning outputs. You can also skip files entirely by assigning inline text (multi-line or prefixed with `inline:`) to workflow prompt properties. Stage keys and placeholders are documented in `docs/indexing-and-query.md`.

See [`docs/indexing-and-query.md`](docs/indexing-and-query.md) for a deeper mapping between the .NET workflows and the research publications underpinning GraphRAG.

---

## Local Cosmos Testing

1. Install and start the [Azure Cosmos DB Emulator](https://learn.microsoft.com/azure/cosmos-db/local-emulator).
2. Export the connection string:
   ```bash
   export COSMOS_EMULATOR_CONNECTION_STRING="AccountEndpoint=https://localhost:8081/;AccountKey=…;"
   ```
3. Rerun `dotnet test`; Cosmos scenarios will seed databases & verify relationships without additional setup.

---

## Development Tips

- **Solution layout.** Use `GraphRag.slnx` in Visual Studio/VS Code/Rider for a complete workspace view.
- **Formatting / analyzers.** Run `dotnet format GraphRag.slnx` before committing to satisfy the repo analyzers.
- **Coding conventions.** 
  - `nullable` and implicit usings are enabled; keep annotations accurate.
  - Async methods should follow the `Async` suffix convention.
  - Prefer DI helpers in `ManagedCode.GraphRag` when wiring new services.
- **Graph adapters.** Implement additional backends by conforming to `IGraphStore` and registering via `IServiceCollection`.

---

## Contributing

1. Fork and clone the repo.
2. Create a feature branch from `main`.
3. Follow the repository rules (build before testing; integration tests must use real containers).
4. Submit a PR referencing any related issues. Include `dotnet test GraphRag.slnx` output in the PR body.

See `CONTRIBUTING.md` for coding standards and PR expectations.

---

## License & Credits

- Licensed under the [MIT License](LICENSE).
- Original Python implementation © Microsoft; see the `graphrag-python` submodule for upstream documentation and examples.

---

Have questions or found a bug? Open an issue or start a discussion—we’re actively evolving the .NET port and welcome feedback. 🚀
