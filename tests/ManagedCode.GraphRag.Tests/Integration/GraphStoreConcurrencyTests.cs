using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Integration;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class GraphStoreConcurrencyTests(GraphRagApplicationFixture fixture)
{
    private const int ParallelClients = 200;

    public static IEnumerable<object[]> Providers => GraphStoreTestProviders.ProviderKeysAndLabels;

    [Theory]
    [MemberData(nameof(Providers))]
    public async Task GraphStores_HandleParallelClientsAsync(string providerKey, string label)
    {
        var store = fixture.Services.GetKeyedService<IGraphStore>(providerKey);
        if (store is null)
        {
            return;
        }

        await store.InitializeAsync();
        var prefix = $"{providerKey}-concurrency-{Guid.NewGuid():N}";
        var rootId = $"{prefix}-root";
        await store.UpsertNodeAsync(rootId, label, new Dictionary<string, object?> { ["seed"] = true });

        var scopeFactory = fixture.Services.GetRequiredService<IServiceScopeFactory>();
        var tasks = Enumerable.Range(0, ParallelClients).Select(index => Task.Run(async () =>
        {
            await using var scope = scopeFactory.CreateAsyncScope();
            var scopedStore = scope.ServiceProvider.GetKeyedService<IGraphStore>(providerKey);
            if (scopedStore is null)
            {
                return;
            }

            var nodeId = $"{prefix}-node-{index:D4}";
            await scopedStore.UpsertNodeAsync(nodeId, label, new Dictionary<string, object?> { ["index"] = index, ["provider"] = providerKey });
            await scopedStore.UpsertNodeAsync(nodeId, label, new Dictionary<string, object?>
            {
                ["index"] = index,
                ["provider"] = providerKey,
                ["version"] = 2,
                ["obsolete"] = null
            });

            await scopedStore.UpsertRelationshipAsync(
                rootId,
                nodeId,
                "CONCURRENT_LINK",
                new Dictionary<string, object?> { ["weight"] = index, ["bucket"] = index % 4 });

            if (index % 5 == 0)
            {
                var batch = new[]
                {
                    new GraphNodeUpsert($"{prefix}-batch-{index:D4}-a", label, new Dictionary<string, object?> { ["owner"] = nodeId }),
                    new GraphNodeUpsert($"{prefix}-batch-{index:D4}-b", label, new Dictionary<string, object?> { ["owner"] = nodeId })
                };
                await scopedStore.UpsertNodesAsync(batch);
            }
        }));

        await Task.WhenAll(tasks);

        var nodes = await CollectNodesAsync(store, prefix);
        Assert.Contains(nodes, node => node.Id == rootId);
        var createdMainNodes = nodes.Count(node => node.Id.StartsWith($"{prefix}-node-", StringComparison.Ordinal));
        Assert.Equal(ParallelClients, createdMainNodes);

        var relationships = await CollectRelationshipsAsync(store, prefix, rootId);
        var concurrentEdges = relationships
            .Where(rel => rel.SourceId == rootId && rel.TargetId.StartsWith($"{prefix}-node-", StringComparison.Ordinal))
            .ToList();
        Assert.Equal(ParallelClients, concurrentEdges.Count);

        var relationshipsToDelete = concurrentEdges
            .Where((_, index) => index % 3 == 0)
            .Select(rel => new GraphRelationshipKey(rel.SourceId, rel.TargetId, rel.Type))
            .ToList();

        foreach (var batch in relationshipsToDelete.Chunk(25))
        {
            await store.DeleteRelationshipsAsync(batch);
        }

        var outgoing = await CollectAsync(store.GetOutgoingRelationshipsAsync(rootId));
        foreach (var key in relationshipsToDelete)
        {
            Assert.DoesNotContain(outgoing, rel => rel.SourceId == key.SourceId && rel.TargetId == key.TargetId && rel.Type == key.Type);
        }

        var batchNodes = nodes
            .Where(node => node.Id.Contains($"{prefix}-batch-", StringComparison.Ordinal))
            .Select(node => node.Id)
            .ToList();

        foreach (var chunk in batchNodes.Chunk(32))
        {
            await store.DeleteNodesAsync(chunk);
        }

        var remainingBatchNodes = await CollectNodesAsync(store, prefix);
        foreach (var removed in batchNodes)
        {
            Assert.DoesNotContain(remainingBatchNodes, node => node.Id == removed);
        }
    }

    private static async Task<List<GraphNode>> CollectNodesAsync(IGraphStore store, string prefix)
    {
        var results = new List<GraphNode>();
        await foreach (var node in store.GetNodesAsync())
        {
            if (node.Id.StartsWith(prefix, StringComparison.Ordinal))
            {
                results.Add(node);
            }
        }

        return results;
    }

    private static async Task<List<GraphRelationship>> CollectRelationshipsAsync(IGraphStore store, string prefix, string rootId)
    {
        var results = new List<GraphRelationship>();
        await foreach (var relationship in store.GetRelationshipsAsync())
        {
            if (relationship.SourceId.StartsWith(prefix, StringComparison.Ordinal) ||
                relationship.TargetId.StartsWith(prefix, StringComparison.Ordinal) ||
                relationship.SourceId == rootId)
            {
                results.Add(relationship);
            }
        }

        return results;
    }

    private static async Task<List<T>> CollectAsync<T>(IAsyncEnumerable<T> source)
    {
        var list = new List<T>();
        await foreach (var item in source)
        {
            list.Add(item);
        }

        return list;
    }
}
