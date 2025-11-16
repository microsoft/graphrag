namespace GraphRag.Graphs;

public interface IGraphStore
{
    Task InitializeAsync(CancellationToken cancellationToken = default);

    Task UpsertNodeAsync(string id, string label, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default);

    Task UpsertNodesAsync(IReadOnlyCollection<GraphNodeUpsert> nodes, CancellationToken cancellationToken = default);

    Task UpsertRelationshipAsync(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default);

    Task UpsertRelationshipsAsync(IReadOnlyCollection<GraphRelationshipUpsert> relationships, CancellationToken cancellationToken = default);

    IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, CancellationToken cancellationToken = default);

    IAsyncEnumerable<GraphNode> GetNodesAsync(GraphTraversalOptions? options = null, CancellationToken cancellationToken = default);

    IAsyncEnumerable<GraphRelationship> GetRelationshipsAsync(GraphTraversalOptions? options = null, CancellationToken cancellationToken = default);
}

public sealed record GraphRelationship(
    string SourceId,
    string TargetId,
    string Type,
    IReadOnlyDictionary<string, object?> Properties);

public sealed record GraphNode(
    string Id,
    string Label,
    IReadOnlyDictionary<string, object?> Properties);

public sealed record GraphTraversalOptions
{
    public int? Skip { get; init; }

    public int? Take { get; init; }

    public void Validate(string? skipParamName = null, string? takeParamName = null)
    {
        if (Skip is < 0)
        {
            throw new ArgumentOutOfRangeException(skipParamName ?? nameof(Skip), Skip, "Skip must be greater than or equal to zero.");
        }

        if (Take is < 0)
        {
            throw new ArgumentOutOfRangeException(takeParamName ?? nameof(Take), Take, "Take must be greater than or equal to zero.");
        }
    }
}
