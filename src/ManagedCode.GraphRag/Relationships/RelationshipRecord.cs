using System.Collections.Immutable;

namespace GraphRag.Relationships;

/// <summary>
/// Represents a finalized relationship row emitted by the GraphRAG pipeline.
/// </summary>
public sealed record RelationshipRecord(
    string Id,
    int HumanReadableId,
    string Source,
    string Target,
    string Type,
    string? Description,
    double Weight,
    int CombinedDegree,
    ImmutableArray<string> TextUnitIds,
    bool Bidirectional);

/// <summary>
/// Represents the minimal information required to seed relationship processing.
/// </summary>
public sealed record RelationshipSeed(
    string Source,
    string Target,
    string? Description,
    double Weight,
    IReadOnlyList<string> TextUnitIds)
{
    public string Type { get; init; } = "related_to";

    public bool Bidirectional { get; init; }
}
