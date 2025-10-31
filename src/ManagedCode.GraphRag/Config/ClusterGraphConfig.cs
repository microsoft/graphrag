namespace GraphRag.Config;

/// <summary>
/// Configuration settings for graph community clustering.
/// </summary>
public sealed class ClusterGraphConfig
{
    /// <summary>
    /// Gets or sets the maximum number of entities allowed in a single community cluster.
    /// A value less than or equal to zero disables the limit.
    /// </summary>
    public int MaxClusterSize { get; set; } = 10;

    /// <summary>
    /// Gets or sets a value indicating whether the largest connected component
    /// should be used when clustering.
    /// </summary>
    public bool UseLargestConnectedComponent { get; set; } = true;

    /// <summary>
    /// Gets or sets the seed used when ordering traversal operations to keep
    /// results deterministic across runs.
    /// </summary>
    public int Seed { get; set; } = unchecked((int)0xDEADBEEF);

    /// <summary>
    /// Gets or sets the maximum number of label propagation iterations when the
    /// <see cref="CommunityDetectionAlgorithm.FastLabelPropagation"/> algorithm is used.
    /// </summary>
    public int MaxIterations { get; set; } = 20;

    /// <summary>
    /// Gets or sets the community detection algorithm. The fast label propagation
    /// implementation mirrors the in-process routine provided by GraphRag.Net.
    /// </summary>
    public CommunityDetectionAlgorithm Algorithm { get; set; }
        = CommunityDetectionAlgorithm.FastLabelPropagation;
}
