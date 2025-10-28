namespace GraphRag.Storage.Postgres;

public sealed class PostgresGraphStoreConfig
{
    public string ConnectionString { get; set; } = string.Empty;

    public string GraphName { get; set; } = "graphrag";

    public bool AutoCreateIndexes { get; set; } = true;

    public Dictionary<string, string[]> VertexPropertyIndexes { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    public Dictionary<string, string[]> EdgePropertyIndexes { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    public bool MakeDefault { get; set; }

}
