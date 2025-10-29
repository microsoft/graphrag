namespace GraphRag.Config;

/// <summary>
/// Represents the root configuration for the GraphRAG pipeline.
/// </summary>
public sealed class GraphRagConfig
{
    public string RootDir { get; set; } = Directory.GetCurrentDirectory();

    public Dictionary<string, LanguageModelConfig> Models { get; set; } = new(StringComparer.OrdinalIgnoreCase)
    {
        ["default_chat_model"] = new LanguageModelConfig(),
        ["default_embedding_model"] = new LanguageModelConfig
        {
            Type = ModelType.Embedding,
            Model = "text-embedding-3-small"
        }
    };

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

    public CacheConfig Cache { get; set; } = new();

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

    public SnapshotsConfig Snapshots { get; set; } = new();

    public Dictionary<string, object?> Extensions { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    public LanguageModelConfig GetLanguageModelConfig(string modelId)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(modelId);
        if (!Models.TryGetValue(modelId, out var config))
        {
            throw new KeyNotFoundException($"Model ID '{modelId}' not found in configuration.");
        }

        return config;
    }

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
