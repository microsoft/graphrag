using System.Collections.Immutable;

namespace GraphRag.Community;

/// <summary>
/// Represents a finalized community row emitted by the GraphRAG pipeline.
/// </summary>
public sealed record CommunityRecord(
    string Id,
    int HumanReadableId,
    int CommunityId,
    int Level,
    int? ParentId,
    ImmutableArray<int> Children,
    string Title,
    ImmutableArray<string> EntityIds,
    ImmutableArray<string> RelationshipIds,
    ImmutableArray<string> TextUnitIds,
    string? Period,
    int Size);
