namespace GraphRag.Config;

public sealed class StorageConfig
{
    public StorageType Type { get; set; } = StorageType.File;

    public string BaseDir { get; set; } = "output";

    public string? ConnectionString { get; set; }

    public string? ContainerName { get; set; }

    public string? StorageAccountBlobUrl { get; set; }

    public string? CosmosDbAccountUrl { get; set; }
}
