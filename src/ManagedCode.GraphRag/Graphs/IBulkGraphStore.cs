namespace GraphRag.Graphs;

public interface IBulkGraphStore
{
    Task UpsertNodesAsync(IReadOnlyCollection<GraphNodeUpsert> nodes, CancellationToken cancellationToken = default);

    Task UpsertRelationshipsAsync(IReadOnlyCollection<GraphRelationshipUpsert> relationships, CancellationToken cancellationToken = default);
}
