namespace GraphRag.Config;

/// <summary>
/// Represents the root configuration for the GraphRAG pipeline.
/// </summary>
public sealed class GraphRagConfig
{
    public string RootDir { get; set; } = Directory.GetCurrentDirectory();

    public HashSet<string> Models { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    public InputConfig Input { get; set; } = new();

    public ChunkingConfig Chunks { get; set; } = new();

    public StorageConfig Output { get; set; } = new();

    public Dictionary<string, StorageConfig>? Outputs { get; set; }
        = new(StringComparer.OrdinalIgnoreCase);

    public StorageConfig UpdateIndexOutput { get; set; } = new()
    {
        BaseDir = "output/update",
        Type = StorageType.File
    };

    public ReportingConfig Reporting { get; set; } = new();

    public Dictionary<string, VectorStoreConfig> VectorStore { get; set; } = new(StringComparer.OrdinalIgnoreCase)
    {
        ["default_vector_store"] = new VectorStoreConfig()
    };

    public List<string>? Workflows { get; set; }
        = new();

    public TextEmbeddingConfig EmbedText { get; set; } = new();

    public ExtractGraphConfig ExtractGraph { get; set; } = new();

    public SummarizeDescriptionsConfig SummarizeDescriptions { get; set; } = new();

    public ClusterGraphConfig ClusterGraph { get; set; } = new();

    public CommunityReportsConfig CommunityReports { get; set; } = new();

    public PromptTuningConfig PromptTuning { get; set; } = new();

    public SnapshotsConfig Snapshots { get; set; } = new();

    public Dictionary<string, object?> Extensions { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    public VectorStoreConfig GetVectorStoreConfig(string vectorStoreId)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(vectorStoreId);
        if (!VectorStore.TryGetValue(vectorStoreId, out var config))
        {
            throw new KeyNotFoundException($"Vector store ID '{vectorStoreId}' not found in configuration.");
        }

        return config;
    }
}
