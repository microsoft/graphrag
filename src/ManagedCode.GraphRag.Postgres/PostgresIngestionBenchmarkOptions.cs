using System;
using System.Collections.Generic;

namespace GraphRag.Storage.Postgres;

public sealed class PostgresIngestionBenchmarkOptions
{
    public string SourceLabel { get; set; } = "Source";

    public string TargetLabel { get; set; } = "Target";

    public string EdgeLabel { get; set; } = "RELATES_TO";

    public string SourceIdColumn { get; set; } = "source_id";

    public string TargetIdColumn { get; set; } = "target_id";

    public Dictionary<string, string> EdgePropertyColumns { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    public bool EnsurePropertyIndexes { get; set; } = true;
}
