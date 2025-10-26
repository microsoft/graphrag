# GraphRAG for .NET

This repository hosts the in-progress C#/.NET 9 migration of Microsoft's GraphRAG project. The original
Python implementation is still available as a git submodule under `submodules/graphrag-python` for
reference while the port matures.

## Repository layout

- `GraphRag.slnx` – experimental solution definition referencing every project in the workspace.
- `Directory.Build.props` / `Directory.Packages.props` – centralised build settings and pinned NuGet package versions.
- `src/GraphRag.Abstractions` – shared interfaces for pipelines, storage, vector indexes, and graph databases.
- `src/GraphRag.Core` – the pipeline builder, service registration helpers, and DI primitives.
- `src/GraphRag.Storage.*` – concrete adapters for Neo4j, Azure Cosmos DB, and PostgreSQL-backed graph storage.
- `tests/GraphRag.Tests.Integration` – Aspire-powered integration tests that exercise the real datastores via xUnit.
- `.github/workflows/dotnet-integration.yml` – GitHub Actions workflow that runs the integration tests on both Linux and Windows agents.

## Prerequisites

- .NET SDK 9.0 preview or newer (the workflow and development container install it via `dotnet-install`).
- Docker Desktop or another container runtime so Aspire can launch Neo4j and PostgreSQL for the tests.
- (Optional) Azure Cosmos DB Emulator running locally with the `COSMOS_EMULATOR_CONNECTION_STRING` environment
  variable populated in order to run the Cosmos integration test.

## Running the tests locally

```bash
dotnet test tests/GraphRag.Tests.Integration/GraphRag.Tests.Integration.csproj --logger "console;verbosity=normal"
```

When the Cosmos emulator is available the test suite will automatically seed it and assert the stored relationship count.
