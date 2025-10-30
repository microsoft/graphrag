# Repository Guidelines

## Rules to follow
- Always run `dotnet build GraphRag.slnx` (or the relevant project) before executing any `dotnet test` command.
- Default to the latest available versions (e.g., Apache AGE `latest`) when selecting dependencies, per user request ("тобі треба latest").
- Do not create or rely on fake database stores (e.g., `FakePostgresGraphStore`); all tests must use real connectors/backing services.
- Keep default prompts in static C# classes; do not rely on prompt files under `prompts/` for built-in templates.
- Register language models through Microsoft.Extensions.AI keyed services; avoid bespoke `LanguageModelConfig` providers.
- Always run `dotnet format GraphRag.slnx` before finishing work.

# Conversations
any resulting updates to agents.md should go under the section "## Rules to follow"
When you see a convincing argument from me on how to solve or do something. add a summary for this in agents.md. so you learn what I want over time.
If I say any of the following point, you do this: add the context to agents.md, and associate this with a specific type of task.
if I say "never do x" in some way.
if I say "always do x" in some way.
if I say "the process is x" in some way.
If I tell you to remember something, you do the same, update


## Project Structure & Module Organization
GraphRag for .NET lives under `src/`. The core pipeline orchestration, abstractions, and DI helpers live in `src/ManagedCode.GraphRag`, while datastore adapters sit in sibling projects (`ManagedCode.GraphRag.CosmosDb`, `ManagedCode.GraphRag.Neo4j`, `ManagedCode.GraphRag.Postgres`). Integration scenarios are covered in `tests/GraphRag.Tests.Integration`, which references all runtime projects and spins up backing services through Aspire. Use `GraphRag.slnx` to load the whole workspace in Visual Studio or `dotnet` commands. The original Python reference implementation remains under `submodules/graphrag-python`—treat it as read-only parity documentation unless a migration task explicitly targets it.

## Build, Test, and Development Commands
Run `dotnet restore GraphRag.slnx` to hydrate packages and the centralized version props. Build with `dotnet build GraphRag.slnx -c Release` before publishing packages. Execute integration tests via `dotnet test tests/GraphRag.Tests.Integration/GraphRag.Tests.Integration.csproj --logger "console;verbosity=normal"`, ensuring Docker Desktop (or compatible) is running so Aspire can provision Neo4j and PostgreSQL containers. Set `COSMOS_EMULATOR_CONNECTION_STRING` if you need Cosmos coverage; the suite skips those checks when the variable is absent. Run `dotnet format GraphRag.slnx` to satisfy analyzers.

## Coding Style & Naming Conventions
The solution targets `net9.0` with `nullable` and `implicit usings` enabled—keep nullability annotations accurate. Follow standard C# conventions (four-space indentation, PascalCase for types, camelCase for locals, async methods suffixed with `Async`). Shared DI entry points live in `ServiceCollectionExtensions`; keep new registration helpers fluent and additive. Centralized package versions are pinned in `Directory.Packages.props`; update there rather than individual project files.

## Testing Guidelines
New tests extend xUnit classes named `<Feature>Tests` under `tests/GraphRag.Tests.Integration`. Group complex orchestration scenarios into nested classes for readability and reuse helper fixtures where Aspire resources are needed. When adding Cosmos-specific tests, guard them with `[Trait("Category", "Cosmos")]` so they can be filtered (`dotnet test ... --filter Category!=Cosmos`) when the emulator is unavailable. Verify new storage integrations against all supported backends and document container images or seed data in the relevant fixture.

## Commit & Pull Request Guidelines
Write imperative, present-tense commit subjects (e.g., `Add Neo4j relationship projection`) and append the GitHub issue/PR number in parentheses when applicable (`(#123)`). Structure PR descriptions with a brief summary, a testing checklist, and required deployment notes (connection strings, migrations, etc.). Link related issues using `Fixes #ID` so automation closes them. Screenshots are optional but helpful for CLI output or diagnostics. Always rerun `dotnet build` and `dotnet test` before requesting review, and mention any intentionally skipped checks.
