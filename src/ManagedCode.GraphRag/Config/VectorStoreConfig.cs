using System.Collections.Generic;

namespace GraphRag.Config;

public sealed class VectorStoreConfig
{
    public VectorStoreType Type { get; set; } = VectorStoreType.LanceDb;

    public string? DbUri { get; set; }
        = "./vector_store";

    public string? Url { get; set; }
        = null;

    public string? ApiKey { get; set; }
        = null;

    public string? Audience { get; set; }
        = null;

    public string ContainerName { get; set; } = "graphrag";

    public string? DatabaseName { get; set; }
        = null;

    public bool Overwrite { get; set; }
        = false;

    public Dictionary<string, VectorStoreSchemaConfig> EmbeddingsSchema { get; set; } = new();
}
