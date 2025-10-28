namespace GraphRag.Data;

public sealed record TextUnitRecord
{
    public required string Id { get; init; }

    public required string Text { get; init; }

    public int TokenCount { get; init; }

    public IReadOnlyList<string> DocumentIds { get; init; } = Array.Empty<string>();

    public IReadOnlyList<string> EntityIds { get; init; } = Array.Empty<string>();

    public IReadOnlyList<string> RelationshipIds { get; init; } = Array.Empty<string>();

    public IReadOnlyList<string> CovariateIds { get; init; } = Array.Empty<string>();
}
