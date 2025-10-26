using System.Collections.Immutable;

namespace GraphRag.Entities;

/// <summary>
/// Represents the finalized state of an entity row emitted by the GraphRAG pipeline.
/// The shape mirrors the columns defined in the original Python data model.
/// </summary>
public sealed record EntityRecord(
    string Id,
    int HumanReadableId,
    string Title,
    string Type,
    string? Description,
    ImmutableArray<string> TextUnitIds,
    int Frequency,
    int Degree,
    double X,
    double Y);

/// <summary>
/// Represents the minimal information required to seed the finalize graph pipeline.
/// </summary>
public sealed record EntitySeed(
    string Title,
    string Type,
    string? Description,
    IReadOnlyList<string> TextUnitIds,
    int Frequency);
