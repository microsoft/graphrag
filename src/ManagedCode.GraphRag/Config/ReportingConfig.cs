namespace GraphRag.Config;

public sealed class ReportingConfig
{
    public ReportingType Type { get; set; } = ReportingType.File;

    public string BaseDir { get; set; } = "reports";

    public string? ConnectionString { get; set; }

    public string? ContainerName { get; set; }

    public string? StorageAccountBlobUrl { get; set; }
}
