namespace GraphRag.Config;

public sealed class VectorStoreConfig
{
    public VectorStoreType Type { get; set; } = VectorStoreType.LanceDb;

    public string? DbUri { get; set; }
        = "./vector_store";

    public string? Url { get; set; }

    public string? ApiKey { get; set; }

    public string? Audience { get; set; }

    public string ContainerName { get; set; } = "graphrag";

    public string? DatabaseName { get; set; }

    public bool Overwrite { get; set; }

    public Dictionary<string, VectorStoreSchemaConfig> EmbeddingsSchema { get; set; } = new();
}
