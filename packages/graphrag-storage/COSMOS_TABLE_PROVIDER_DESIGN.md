# CosmosTableProvider Design

## Status

**Implemented.** Core provider, factory wiring, pipeline refactoring, and simplified
key-value storage are complete. Tested against the Cosmos DB Linux emulator (vNext).
The `graphrag migrate-cosmos` CLI tool is planned but not yet built.

## Problem Statement

The current `AzureCosmosStorage` shoehorns Cosmos DB into a blob/file `Storage` abstraction.
This causes:

| Issue | Impact |
|-------|--------|
| Parquet round-trip: DataFrame → parquet → DataFrame → JSON → Cosmos → reverse | 4 serde hops per read and write |
| Every document is its own partition (`/id`) | All queries are cross-partition fan-outs — the most expensive Cosmos pattern |
| Entity-specific hacks in the storage layer (`if prefix == "entities":`) | Domain logic leaking into generic abstraction |
| `child()` is a no-op (`return self`) | Update runs have no namespace isolation — delta/previous collide |
| `clear()` drops the entire database | No granularity control |
| Sync SDK used inside async methods | Blocks the event loop |
| Non-parameterized f-string queries | SQL injection surface (suppressed with noqa) |

## Design: `CosmosTableProvider`

Implement `TableProvider` directly for Cosmos DB, bypassing the `Storage` layer entirely for tabular data.

### Architecture

```
                      ┌─────────────────────────────┐
                      │     PipelineRunContext       │
                      ├──────────┬──────────────────┤
                      │ Storage  │  TableProvider    │
                      │(kv only) │                   │
                      ├──────────┼──────────────────┤
  File/Blob backend → │file_stor │ ParquetTableProv │ ← File/Blob pipeline
                      ├──────────┼──────────────────┤
  Cosmos backend    → │cosmos_kv │ CosmosTableProv  │ ← Cosmos pipeline
                      │(metadata)│  (native docs)   │
                      └──────────┴──────────────────┘
```

### Cosmos Document Schema

**Container:** single container (configurable, default `graphrag`)  
**Partition key:** `/namespace`

```json
{
    "id":         "entities:42",
    "namespace":  "output",
    "table_name": "entities",
    
    "name":       "JOHN DOE",
    "type":       "PERSON",
    "description": "A character in ...",
    "human_readable_id": 42
}
```

| Field | Purpose | Indexed |
|-------|---------|---------|
| `id` | Unique within namespace. Format: `{table_name}:{row_key}` | Yes (built-in) |
| `namespace` | Partition key. Isolation boundary for child() hierarchy | Yes (partition key) |
| `table_name` | Discriminator for per-table queries within a namespace | Yes (composite index) |
| All other fields | DataFrame columns stored as top-level document properties | Configurable |

### Namespace Mapping

```
output_table_provider            → namespace = ""  (root / default)
update/20260511/delta            → namespace = "20260511/delta"
update/20260511/previous         → namespace = "20260511/previous"
```

`child("delta")` returns a new `CosmosTableProvider` sharing the same client, with namespace extended.

### Query Patterns (All Single-Partition)

| Operation | Query | Partition |
|-----------|-------|-----------|
| `read_dataframe("entities")` | `SELECT * FROM c WHERE c.table_name = 'entities'` | `namespace` |
| `write_dataframe("entities", df)` | Bulk upsert with `namespace` and `table_name` set | `namespace` |
| `has("entities")` | `SELECT VALUE COUNT(1) FROM c WHERE c.table_name = 'entities'` | `namespace` |
| `list()` | `SELECT DISTINCT VALUE c.table_name FROM c` | `namespace` |
| `clear()` | Delete all docs in namespace partition | `namespace` |

**Zero cross-partition queries.** Every query targets a single `namespace` partition.

### Row Identity

Each row needs a stable Cosmos `id`. Strategy per table:

- If the DataFrame has an `id` column: use `{table_name}:{id}`
- Otherwise: use `{table_name}:{index}` (positional)

The pipeline's `id` column is preserved as a regular document property. Cosmos's `id` is the synthetic key above. No column renaming — the pipeline's `id` and Cosmos's `id` happen to share the field, but we store the pipeline value in a separate `_row_id` field if collision occurs.

**Simpler approach chosen:** always store pipeline `id` (if present) as `row_id`, and use `{table_name}:{human_readable_id or index}` as Cosmos `id`. This avoids all the entity-specific hacks in the current implementation.

### Streaming (Table.open())

`CosmosTable` implements the `Table` ABC:

- `__aiter__`: pages through `query_items()` using the async SDK, yields rows one at a time
- `write(row)`: accumulates rows in memory (same as `ParquetTable`)
- `close()`: bulk upserts accumulated rows
- `has(row_id)`: point-read by `id` within namespace (single RU)

True server-side streaming — no full-DataFrame materialization on read unless `read_dataframe()` is called.

## Changes (Implemented)

### 1. `child()` added to `TableProvider` ABC

Non-abstract method with default no-op. Backward compatible — no existing code breaks.

### 2. `ParquetTableProvider.child()` and `CSVTableProvider.child()`

Both delegate to their underlying `Storage.child()`. Existing File/Blob pipelines
work identically.

### 3. `CosmosTableProvider` class — `cosmos_table_provider.py` (~320 lines)

Implements `TableProvider` directly. Owns an async `CosmosClient` (`azure.cosmos.aio`).
No `Storage` dependency.

Key features:
- Lazy container creation via `_ensure_container()` (async init deferred from `__init__`)
- `child()` returns a new instance sharing the same client with extended namespace
- Legacy fallback reads from old `AzureCosmosStorage` containers (when `legacy_container` configured)
- `_LazyCosmosTable` wrapper to bridge synchronous `open()` with async container init

### 4. `CosmosTable` class — `cosmos_table.py` (~160 lines)

Implements `Table` ABC for streaming row access:
- `__aiter__`: async iteration with server-side pagination via `by_page()`
- `length()`: single-partition COUNT query
- `has()`: point-read by composite id
- `write()` / `close()`: accumulate-then-upsert pattern (same as `ParquetTable`)
- `_delete_table_docs()`: truncate before overwrite

### 5. Factory and config wiring

- `TableType.CosmosDB = "cosmosdb"` added to enum
- `TableProviderConfig` gained: `connection_string`, `account_url`, `database_name`,
  `container_name`, `legacy_container` fields
- `table_provider_factory.py` lazy-registers `CosmosTableProvider` on `cosmosdb` type

### 6. Pipeline wiring refactored

`run_pipeline.py` and `get_update_table_providers()` in `utils.py` now use
`table_provider.child()` to build delta/previous providers instead of
`Storage.child()` → `create_table_provider()`.

For Parquet/CSV: `child()` delegates to `Storage.child()`, identical behavior.
For Cosmos: `child()` extends the namespace string. Same API, different isolation mechanism.

### 7. `AzureCosmosStorage` simplified to key-value only (~200 lines, was ~440)

Removed:
- All parquet decomposition/recomposition logic
- Entity-specific `if prefix == "entities":` hacks
- `_no_id_prefixes` tracking
- `pandas` / `BytesIO` / `StringIO` imports
- `_query_all_items` / `_query_count` helper methods
- `_get_prefix` method
- `graphrag.logger.progress` import

Added:
- Working `child()` via namespace prefix (separator: `:` — see caveat below)
- Scoped `clear()`: container drop-and-recreate for root, prefix-query-and-delete for children
- `keys()` implementation (was `raise NotImplementedError`)

## Implementation Caveats Discovered During Testing

### Cosmos DB document IDs cannot contain `/`

The Azure Cosmos DB SDK uses the document `id` as part of the REST URL path
(e.g. `/dbs/{db}/colls/{coll}/docs/{id}`). If `id` contains `/`, the SDK
interprets it as additional path segments and the request fails with
`"Id contains illegal chars."` on write or HTTP 400 on read.

**Impact on `AzureCosmosStorage`:** The key-value store uses `id` as the
partition key (`/id`). `child()` namespacing must NOT use `/` as separator.
We use `:` instead: `child("cache").child("gpt4o")` produces keys like
`cache:gpt4o:abc123`.

**Impact on `CosmosTableProvider`:** No impact. The namespace is stored in a
separate `namespace` field (the partition key is `/namespace`), and the
document `id` uses the format `{table_name}:{row_key}` with `:` as
separator. The namespace value itself can contain `/` freely because
it's a partition key value, not a document id.

### `list()` is synchronous in the ABC but Cosmos queries are async

The `TableProvider.list()` method is declared synchronous (no `async`). The
Cosmos implementation needs to run an async query. We solve this with
`_list_async()` and a sync wrapper that detects whether an event loop is
running, using a thread pool executor as fallback. This matches the pattern
used elsewhere in the codebase.

### `enable_cross_partition_query` doesn't work in async SDK (v4.9)

The async SDK (`azure.cosmos.aio`) leaks `enable_cross_partition_query` through
to `aiohttp.ClientSession._request()`, causing a `TypeError`. This affects
legacy fallback reads which must do cross-partition queries against old containers
(partition key `/id`).

**Workaround:** Omit `enable_cross_partition_query` entirely and don't set
`partition_key`. When `partition_key` is omitted, the async SDK automatically
performs a cross-partition query. New-schema queries are unaffected because they
always target a single namespace partition.

## What We Get

| Before | After |
|--------|-------|
| 4 serde hops per read/write | 1 hop (DataFrame ↔ Cosmos docs directly) |
| All cross-partition queries | All single-partition queries |
| Entity-specific hacks in storage layer | No domain logic in storage layer |
| `child()` broken (no-op) | `child()` works via namespace partitioning |
| `clear()` drops entire database | `clear()` scopes to namespace partition |
| Sync SDK blocking event loop | Async SDK throughout |
| Non-parameterized queries | All queries parameterized |
| ~440 lines of workaround code | ~950 lines total (326 kv-storage + 453 table-provider + 171 table) — clean, idiomatic Cosmos code |
| Parquet as intermediate format | No parquet involved for Cosmos path |
| No streaming capability | True server-side pagination in `CosmosTable` |

## What We Don't Change

- `Storage` ABC — untouched
- `FileStorage`, `AzureBlobStorage`, `MemoryStorage` — untouched
- `ParquetTableProvider`, `CSVTableProvider` — gain `child()`, otherwise untouched
- Pipeline workflows — untouched (they call `TableProvider` methods, not `Storage`)
- `JsonCache` — untouched (uses `Storage.child()`, separate from table provider)
- Input readers (`graphrag-input`) — untouched (use `Storage` directly)

## Migration / Backward Compatibility

### The Hard Constraint: Partition Keys Are Immutable

The current container uses `/id` as its partition key. The new schema requires `/namespace`.
**Cosmos DB does not allow changing a container's partition key after creation.**
This means migration requires a new container — you cannot transform documents in-place.

### Legacy Document Schemas (Current `AzureCosmosStorage`)

There are three document shapes in the old container, all sharing partition key `/id`:

```
# Shape 1: Tabular row (non-entity)
{"id": "relationships:42", "source": "A", "target": "B", "weight": 0.8, ...}
                 ↑ partition key = "relationships:42"

# Shape 2: Tabular row (entity — special-cased)
{"id": "entities:7", "entity_id": "abc-uuid", "human_readable_id": 7, "name": "FOO", ...}
                ↑ partition key = "entities:7"
                   ↑ pipeline's real id, renamed to avoid collision

# Shape 3: Key-value metadata
{"id": "context.json", "body": {"step": "extract_graph", ...}}
                  ↑ partition key = "context.json"
```

### New Document Schema (CosmosTableProvider)

Single container, partition key `/namespace`:

```
# Shape 1 & 2 unified: Tabular row (all tables, no special cases)
{"id": "entities:7", "namespace": "output", "table_name": "entities",
 "row_id": "abc-uuid", "human_readable_id": 7, "name": "FOO", ...}
                      ↑ partition key = "output"

# Shape 3: Unchanged, stays in simplified AzureCosmosStorage (separate container)
{"id": "context.json", "body": {"step": "extract_graph", ...}}
```

### Migration Scenarios

| Scenario | User Action | Migration Needed |
|----------|-------------|------------------|
| **Fresh install** (no existing data) | Set `table_provider.type: cosmosdb` in config | None — new container created automatically |
| **Existing File/Blob → Cosmos** | Change config, re-index | None — fresh write to new container |
| **Existing Cosmos data (legacy)** | Change config, run `graphrag migrate-cosmos` | Yes — see below |
| **Stay on current Cosmos impl** | No config change | None — old code still works |

### Migration Strategy: Dual-Container with CLI Tool

#### Container Layout (Post-Migration)

```
Database: graphrag
├── Container: graphrag-kv      ← simplified AzureCosmosStorage (partition key: /id)
│   ├── {"id": "context.json", "body": {...}}
│   ├── {"id": "stats.json", "body": {...}}
│   └── {"id": "report.graphml", "body": "..."}
│
└── Container: graphrag-tables  ← CosmosTableProvider (partition key: /namespace)
    ├── {"id": "entities:0", "namespace": "output", "table_name": "entities", ...}
    ├── {"id": "entities:1", "namespace": "output", "table_name": "entities", ...}
    ├── {"id": "relationships:0", "namespace": "output", "table_name": "relationships", ...}
    └── ...
```

Separation is natural: the key-value data (context, stats, graphml, cache) has trivially
small volume and the `/id` partition key is fine for point-reads. Tabular data benefits
from the `/namespace` partition key for efficient scans.

#### CLI Migration Command

```bash
graphrag migrate-cosmos \
  --account-url https://myaccount.documents.azure.com:443/ \
  --database graphrag \
  --legacy-container graphrag-output \
  --target-container graphrag-tables \
  --namespace output
```

The tool:
1. Connects to the legacy container (partition key `/id`)
2. Discovers all `{prefix}:*` documents via cross-partition query (one final fan-out)
3. Groups documents by prefix → table name
4. For each table:
   - Reverses entity-specific hacks (`entity_id` → `row_id`, etc.)
   - Adds `namespace` and `table_name` fields
   - Bulk-upserts into the target container (partition key `/namespace`)
5. Copies key-value documents (`context.json`, `stats.json`, etc.) to the kv container
6. Prints a summary: tables migrated, row counts, RU consumption
7. Does NOT delete the legacy container (user does that manually after verification)

#### Transparent Fallback (Read-Time Compat)

For users who switch config before running the migration tool, `CosmosTableProvider`
includes a **read-time fallback**:

1. `read_dataframe("entities")` queries the new container first
2. If the table is empty/missing AND a `legacy_container` is configured, falls back
   to reading from the legacy container using the old `{prefix}:*` query pattern
3. Normalizes the legacy documents (strip prefix from id, reverse entity hacks,
   add `namespace`/`table_name`) and returns the DataFrame
4. Logs a warning: `"Reading from legacy container — run 'graphrag migrate-cosmos' to complete migration"`
5. Does NOT auto-write to the new container (migration is explicit, not side-effect)

This means:
- **Reads work immediately** after config change, even without running migration
- **Writes always go to the new container** with the new schema
- **A re-index** (which reads then writes everything) effectively migrates all data
- The explicit migration tool is for users who want to migrate without re-indexing

#### Config Change Required

```yaml
# Before (legacy)
output_storage:
  type: cosmosdb
  account_url: https://myaccount.documents.azure.com:443/
  database_name: graphrag
  container_name: graphrag-output

# After (new)
output_storage:
  type: cosmosdb                           # simplified to key-value only
  account_url: https://myaccount.documents.azure.com:443/
  database_name: graphrag
  container_name: graphrag-kv              # new container for metadata

table_provider:
  type: cosmosdb                           # NEW - routes to CosmosTableProvider
  container_name: graphrag-tables          # table-specific: new container for tabular data
  legacy_container: graphrag-output        # table-specific: optional migration fallback
```

Connection details (`account_url`, `connection_string`, `database_name`) are NOT
duplicated on `table_provider`. The factory extracts them from `output_storage`
automatically when `table_provider.type` is `cosmosdb`.

When `legacy_container` is set, the fallback read path is active. Once migration is
complete and verified, the user removes `legacy_container` from config and optionally
deletes the old container.

#### Migration Safety

- **Idempotent:** Running the migration tool multiple times is safe (upsert semantics)
- **Non-destructive:** Legacy container is never modified or deleted by the tool
- **Resumable:** If interrupted, re-run picks up where it left off (upserts are atomic)
- **Verifiable:** Tool prints row counts per table; user can compare against legacy
- **Rollback:** If anything goes wrong, delete the new container and revert config

#### What Happens to Cache Data?

LLM cache data (`JsonCache`) uses `Storage.child()` for namespacing. This stays on the
`AzureCosmosStorage` (key-value) path. Cache documents are small JSON blobs with
`{"id": key, "body": {...}}` format — they work fine with `/id` as partition key since
they're always accessed by point-read. No migration needed for cache data.

If the user was previously using a single container for both cache and output, the
migration tool separates them: tabular data goes to `graphrag-tables`, key-value data
(including cache) stays in the legacy container (or moves to `graphrag-kv`).

## Tables

7 tables managed by the provider:

`documents`, `text_units`, `entities`, `relationships`, `covariates`, `communities`, `community_reports`

Embeddings are written via table provider as `embeddings.{name}` — these become `table_name = "embeddings.entity_description"` etc.

## File Inventory

| File | Action | Status |
|------|--------|--------|
| `graphrag_storage/tables/table_provider.py` | Add `child()` default method | ✅ Done |
| `graphrag_storage/tables/table_type.py` | Add `CosmosDB` enum value | ✅ Done |
| `graphrag_storage/tables/table_provider_config.py` | Add Cosmos + legacy_container fields | ✅ Done |
| `graphrag_storage/tables/cosmos_table_provider.py` | **New** — main implementation (453 lines) | ✅ Done |
| `graphrag_storage/tables/cosmos_table.py` | **New** — streaming Table impl (171 lines) | ✅ Done |
| `graphrag_storage/tables/table_provider_factory.py` | Add cosmosdb case | ✅ Done |
| `graphrag_storage/tables/parquet_table_provider.py` | Add `child()` method | ✅ Done |
| `graphrag_storage/tables/csv_table_provider.py` | Add `child()` method | ✅ Done |
| `graphrag_storage/azure_cosmos_storage.py` | Simplified to key-value only (326 lines) | ✅ Done |
| `graphrag/index/run/utils.py` | Refactor `get_update_table_providers` | ✅ Done |
| `graphrag/index/run/run_pipeline.py` | Use `table_provider.child()` for update runs | ✅ Done |
| `graphrag/cli/migrate_cosmos.py` | **New** — CLI migration tool | ⬜ Planned |
| `graphrag/cli/main.py` | Register `migrate-cosmos` subcommand | ⬜ Planned |

## Testing

### Unit / verb tests

302 unit tests + 15 verb tests pass (unchanged from baseline). The pipeline
wiring refactor is backward-compatible for File/Blob/Memory backends.

### E2E tests against Cosmos emulator

Tested against `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview`
(ARM64-compatible, vNext emulator using HTTP on port 8081).

| Test | Checks | Status |
|------|--------|--------|
| CosmosTableProvider lifecycle | write, read, has, list, child, open, stream, truncate | ✅ 11/11 |
| AzureCosmosStorage key-value | set, get, has, child, keys, delete, clear | ✅ 7/7 |
| Factory wiring | config → CosmosTableProvider, child() | ✅ 3/3 |
| Update run simulation | delta/previous/output namespace isolation, merge | ✅ 7/7 |
