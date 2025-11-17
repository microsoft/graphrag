using System.Globalization;
using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Integration;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class GraphStoreProviderParityTests(GraphRagApplicationFixture fixture)
{
    public static IEnumerable<object[]> Providers => GraphStoreTestProviders.ProviderKeysAndLabels;

    [Theory]
    [MemberData(nameof(Providers))]
    public async Task GraphStores_ExecuteFullCrudFlows(string providerKey, string label)
    {
        var store = fixture.Services.GetKeyedService<IGraphStore>(providerKey);
        if (store is null)
        {
            return;
        }

        await store.InitializeAsync();
        var prefix = $"{providerKey}-flow-{Guid.NewGuid():N}";
        var rootId = $"{prefix}-root";
        var neighborId = $"{prefix}-neighbor";

        await store.UpsertNodeAsync(rootId, label, new Dictionary<string, object?> { ["name"] = "root", ["count"] = 1 });
        await store.UpsertNodeAsync(neighborId, label, new Dictionary<string, object?> { ["name"] = "neighbor", ["count"] = 2 });

        await store.UpsertNodeAsync(rootId, label, new Dictionary<string, object?> { ["name"] = null, ["count"] = 3, ["updated"] = true });
        var rootNode = await FindNodeAsync(store, rootId);
        Assert.NotNull(rootNode);
        Assert.Equal(3, Convert.ToInt32(rootNode!.Properties["count"], CultureInfo.InvariantCulture));
        Assert.False(rootNode.Properties.ContainsKey("name"));

        var batchedNodes = Enumerable.Range(0, 5)
            .Select(index => new GraphNodeUpsert(
                $"{prefix}-extra-{index:D2}",
                label,
                new Dictionary<string, object?> { ["index"] = index, ["origin"] = providerKey }))
            .ToList();

        await store.UpsertNodesAsync(batchedNodes);
        foreach (var node in batchedNodes)
        {
            Assert.NotNull(await FindNodeAsync(store, node.Id));
        }

        var relationships = new List<GraphRelationshipUpsert>
        {
            new(rootId, neighborId, "LINKS", new Dictionary<string, object?> { ["weight"] = 0.5 }),
            new(neighborId, rootId, "LINKS", new Dictionary<string, object?> { ["weight"] = 0.6 }, Bidirectional: true)
        };

        await store.UpsertRelationshipsAsync(relationships);
        var outgoing = await CollectAsync(store.GetOutgoingRelationshipsAsync(rootId));
        Assert.Contains(outgoing, rel => rel.TargetId == neighborId && rel.Type == "LINKS");

        var additionalKeys = outgoing
            .Where(rel => rel.TargetId.StartsWith(prefix, StringComparison.Ordinal))
            .Select(rel => new GraphRelationshipKey(rel.SourceId, rel.TargetId, rel.Type))
            .ToList();
        if (additionalKeys.Count > 0)
        {
            await store.DeleteRelationshipsAsync(additionalKeys);
        }

        var relationshipCheck = await CollectAsync(store.GetOutgoingRelationshipsAsync(rootId));
        foreach (var key in additionalKeys)
        {
            Assert.DoesNotContain(relationshipCheck, rel => rel.SourceId == key.SourceId && rel.TargetId == key.TargetId && rel.Type == key.Type);
        }

        var nodesToDelete = batchedNodes.Select(node => node.Id).Append(neighborId).ToList();
        if (nodesToDelete.Count > 0)
        {
            await store.DeleteNodesAsync(nodesToDelete);
        }

        foreach (var nodeId in nodesToDelete)
        {
            Assert.Null(await FindNodeAsync(store, nodeId));
        }
    }

    [Theory]
    [MemberData(nameof(Providers))]
    public async Task GraphStores_HandleNodeInjectionPayloads(string providerKey, string label)
    {
        var store = fixture.Services.GetKeyedService<IGraphStore>(providerKey);
        if (store is null)
        {
            return;
        }

        await store.InitializeAsync();
        var sentinelId = $"{providerKey}-sentinel-{Guid.NewGuid():N}";
        await store.UpsertNodeAsync(sentinelId, label, new Dictionary<string, object?> { ["role"] = "sentinel" });

        var payload = "\" }) MATCH (victim) DETACH DELETE victim //";
        var nodeId = $"{providerKey}-inject-{Guid.NewGuid():N}";
        await store.UpsertNodeAsync(nodeId, label, new Dictionary<string, object?> { ["bio"] = payload });

        var stored = await FindNodeAsync(store, nodeId);
        Assert.NotNull(stored);
        Assert.Equal(payload, stored!.Properties["bio"]?.ToString());

        var sentinel = await FindNodeAsync(store, sentinelId);
        Assert.NotNull(sentinel);
    }

    [Theory]
    [MemberData(nameof(Providers))]
    public async Task GraphStores_HandleRelationshipInjectionPayloads(string providerKey, string label)
    {
        var store = fixture.Services.GetKeyedService<IGraphStore>(providerKey);
        if (store is null)
        {
            return;
        }

        await store.InitializeAsync();
        var sourceId = $"{providerKey}-inj-src-{Guid.NewGuid():N}";
        var targetId = $"{providerKey}-inj-dst-{Guid.NewGuid():N}";

        await store.UpsertNodeAsync(sourceId, label, new Dictionary<string, object?>());
        await store.UpsertNodeAsync(targetId, label, new Dictionary<string, object?>());

        var maliciousWeight = "0.99 }) MATCH (m) DETACH DELETE m //";
        await store.UpsertRelationshipAsync(sourceId, targetId, "TRANSFERRED", new Dictionary<string, object?> { ["weight"] = maliciousWeight, ["flag"] = false });

        var relationships = await CollectAsync(store.GetOutgoingRelationshipsAsync(sourceId));
        var stored = Assert.Single(relationships, rel => rel.TargetId == targetId);
        Assert.Equal(maliciousWeight, stored.Properties["weight"]?.ToString());
        Assert.False(Convert.ToBoolean(stored.Properties["flag"], CultureInfo.InvariantCulture));

        var targetNode = await FindNodeAsync(store, targetId);
        Assert.NotNull(targetNode);
    }

    private static async Task<List<T>> CollectAsync<T>(IAsyncEnumerable<T> source)
    {
        var results = new List<T>();
        await foreach (var item in source)
        {
            results.Add(item);
        }

        return results;
    }

    private static async Task<GraphNode?> FindNodeAsync(IGraphStore store, string nodeId)
    {
        await foreach (var node in store.GetNodesAsync())
        {
            if (node.Id == nodeId)
            {
                return node;
            }
        }

        return null;
    }
}
