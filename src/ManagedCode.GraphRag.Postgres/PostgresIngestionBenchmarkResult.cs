using System;

namespace GraphRag.Storage.Postgres;

public sealed record PostgresIngestionBenchmarkResult(
    int NodesWritten,
    int RelationshipsWritten,
    TimeSpan Duration,
    bool PropertyIndexesEnsured);
