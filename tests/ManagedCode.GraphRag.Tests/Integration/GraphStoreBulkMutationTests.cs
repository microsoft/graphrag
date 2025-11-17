using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Integration;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class GraphStoreBulkMutationTests(GraphRagApplicationFixture fixture)
{
    private readonly GraphRagApplicationFixture _fixture = fixture;

    public static IEnumerable<object[]> Providers => GraphStoreTestProviders.ProviderKeysAndLabels;

    [Theory]
    [MemberData(nameof(Providers))]
    public async Task GraphStores_HandleBulkInsertionAndDeletionAsync(string providerKey, string label)
    {
        var store = _fixture.Services.GetKeyedService<IGraphStore>(providerKey);
        if (store is null)
        {
            return;
        }

        await store.InitializeAsync();
        var prefix = $"{providerKey}-bulk-{Guid.NewGuid():N}";
        var nodes = CreateNodes(prefix, label, 80);

        foreach (var batch in Partition(nodes, 16))
        {
            await store.UpsertNodesAsync(batch);
        }

        var relationships = CreateRelationships(nodes);
        foreach (var batch in Partition(relationships, 16))
        {
            await store.UpsertRelationshipsAsync(batch);
        }

        var storedNodes = await CollectNodesAsync(store, prefix);
        Assert.Equal(nodes.Count, storedNodes.Count);

        var storedRelationships = await CollectRelationshipsAsync(store, prefix);
        Assert.Equal(relationships.Count, storedRelationships.Count);

        var relationshipsToDelete = relationships
            .Where((_, index) => index % 2 == 0)
            .Select(rel => new GraphRelationshipKey(rel.SourceId, rel.TargetId, rel.Type))
            .ToList();

        foreach (var batch in Partition(relationshipsToDelete, 16))
        {
            await store.DeleteRelationshipsAsync(batch);
        }

        var remainingRelationships = await CollectRelationshipsAsync(store, prefix);
        foreach (var removed in relationshipsToDelete)
        {
            Assert.DoesNotContain(
                remainingRelationships,
                rel => rel.SourceId == removed.SourceId && rel.TargetId == removed.TargetId && rel.Type == removed.Type);
        }

        var nodeIds = nodes.Select(node => node.Id).ToList();
        foreach (var batch in Partition(nodeIds, 16))
        {
            await store.DeleteNodesAsync(batch);
        }

        var nodesAfterDelete = await CollectNodesAsync(store, prefix);
        Assert.Empty(nodesAfterDelete);
    }

    private static List<GraphNodeUpsert> CreateNodes(string prefix, string label, int count)
    {
        var nodes = new List<GraphNodeUpsert>(count);
        for (var i = 0; i < count; i++)
        {
            nodes.Add(new GraphNodeUpsert(
                $"{prefix}-node-{i:D4}",
                label,
                new Dictionary<string, object?>
                {
                    ["index"] = i,
                    ["payload"] = $"payload-{i}"
                }));
        }

        return nodes;
    }

    private static List<GraphRelationshipUpsert> CreateRelationships(IReadOnlyList<GraphNodeUpsert> nodes)
    {
        var relationships = new List<GraphRelationshipUpsert>();
        if (nodes.Count == 0)
        {
            return relationships;
        }

        var root = nodes[0];
        for (var i = 1; i < nodes.Count; i++)
        {
            var target = nodes[i];
            relationships.Add(new GraphRelationshipUpsert(
                root.Id,
                target.Id,
                "BULK_CONNECTS",
                new Dictionary<string, object?> { ["weight"] = i }));
        }

        for (var i = 1; i < nodes.Count; i++)
        {
            var source = nodes[i - 1];
            var target = nodes[i];

            relationships.Add(new GraphRelationshipUpsert(
                source.Id,
                target.Id,
                "CHAIN_CONNECTS",
                new Dictionary<string, object?> { ["step"] = i }));
        }

        return relationships;
    }

    private static IEnumerable<IReadOnlyCollection<T>> Partition<T>(IReadOnlyList<T> source, int batchSize)
    {
        if (source.Count == 0)
        {
            yield break;
        }

        for (var i = 0; i < source.Count; i += batchSize)
        {
            yield return source.Skip(i).Take(batchSize).ToList();
        }
    }

    private static async Task<List<GraphNode>> CollectNodesAsync(IGraphStore store, string prefix, CancellationToken cancellationToken = default)
    {
        var nodes = new List<GraphNode>();
        await foreach (var node in store.GetNodesAsync(cancellationToken: cancellationToken))
        {
            if (node.Id.StartsWith(prefix, StringComparison.Ordinal))
            {
                nodes.Add(node);
            }
        }

        return nodes;
    }

    private static async Task<List<GraphRelationship>> CollectRelationshipsAsync(IGraphStore store, string prefix, CancellationToken cancellationToken = default)
    {
        var relationships = new List<GraphRelationship>();
        await foreach (var relationship in store.GetRelationshipsAsync(cancellationToken: cancellationToken))
        {
            if (relationship.SourceId.StartsWith(prefix, StringComparison.Ordinal) ||
                relationship.TargetId.StartsWith(prefix, StringComparison.Ordinal))
            {
                relationships.Add(relationship);
            }
        }

        return relationships;
    }
}
