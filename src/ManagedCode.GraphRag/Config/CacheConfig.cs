namespace GraphRag.Config;

public sealed class CacheConfig
{
    public CacheType Type { get; set; } = CacheType.File;

    public string BaseDir { get; set; } = "cache";

    public string? ConnectionString { get; set; }

    public string? ContainerName { get; set; }

    public string? StorageAccountBlobUrl { get; set; }

    public string? CosmosDbAccountUrl { get; set; }
}
