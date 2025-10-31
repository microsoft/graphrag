namespace GraphRag.Config;

/// <summary>
/// Represents heuristic controls that fine-tune ingestion and graph maintenance behavior.
/// The defaults mirror the semantics implemented in the GraphRag.Net demo service where
/// ingestion aggressively deduplicates, trims by token budgets, and repairs sparse graphs.
/// </summary>
public sealed class HeuristicMaintenanceConfig
{
    /// <summary>
    /// Gets or sets a value indicating whether semantic deduplication should be applied
    /// to text units produced during ingestion. When enabled, text chunks that are deemed
    /// near-duplicates are merged so downstream LLM prompts are not wasted on redundant
    /// context.
    /// </summary>
    public bool EnableSemanticDeduplication { get; set; } = true;

    /// <summary>
    /// Gets or sets the cosine similarity threshold used when merging duplicate text units.
    /// Values should fall within [0,1]; higher values keep the deduplication stricter.
    /// </summary>
    public double SemanticDeduplicationThreshold { get; set; } = 0.92;

    /// <summary>
    /// Gets or sets the maximum number of tokens permitted within a single text unit.
    /// Oversized chunks are discarded to keep prompts within model context limits.
    /// </summary>
    public int MaxTokensPerTextUnit { get; set; } = 1400;

    /// <summary>
    /// Gets or sets the maximum cumulative token budget allocated to each document during
    /// ingestion. Set to a value less than or equal to zero to disable document level trimming.
    /// </summary>
    public int MaxDocumentTokenBudget { get; set; } = 6000;

    /// <summary>
    /// Gets or sets the maximum number of text units that should remain attached to a
    /// relationship when persisting graph edges. Excess associations are trimmed to keep
    /// follow-up prompts compact.
    /// </summary>
    public int MaxTextUnitsPerRelationship { get; set; } = 6;

    /// <summary>
    /// Gets or sets the minimum amount of overlap (expressed as a ratio) required when linking
    /// orphan entities. The ratio compares shared text units against the smaller of the
    /// participating entity sets.
    /// </summary>
    public double OrphanLinkMinimumOverlap { get; set; } = 0.2;

    /// <summary>
    /// Gets or sets the default weight assigned to synthetic orphan relationships.
    /// </summary>
    public double OrphanLinkWeight { get; set; } = 0.35;

    /// <summary>
    /// Gets or sets a value indicating whether relationship heuristics should normalise,
    /// validate, and enhance extracted edges.
    /// </summary>
    public bool EnhanceRelationships { get; set; } = true;

    /// <summary>
    /// Gets or sets the minimum weight enforced when relationship heuristics run. Extracted
    /// relationships that fall below this floor (after normalisation) are bumped up so they
    /// remain queryable.
    /// </summary>
    public double RelationshipConfidenceFloor { get; set; } = 0.35;

    /// <summary>
    /// Gets or sets the minimum overlap (in tokens) required when chunking source documents.
    /// </summary>
    public int MinimumChunkOverlap { get; set; } = 80;

    /// <summary>
    /// Gets or sets an optional keyed model id used to resolve a text embedding generator.
    /// When not supplied, the pipeline falls back to <see cref="TextEmbeddingConfig.ModelId"/>.
    /// </summary>
    public string? EmbeddingModelId { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether orphan entities should be linked back into the
    /// graph using co-occurrence heuristics.
    /// </summary>
    public bool LinkOrphanEntities { get; set; } = true;
}
