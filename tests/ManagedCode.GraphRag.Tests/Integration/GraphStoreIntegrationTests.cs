using System.Globalization;
using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Integration;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class GraphStoreIntegrationTests(GraphRagApplicationFixture fixture)
{
    private static readonly IReadOnlyDictionary<string, string> ProviderLabels = new Dictionary<string, string>
    {
        ["neo4j"] = "Person",
        ["postgres"] = "Chapter",
        ["janus"] = "Person"
    };

    public static IEnumerable<object[]> GraphProviders => ProviderLabels.Keys.Select(key => new object[] { key });

    [Theory]
    [MemberData(nameof(GraphProviders))]
    public async Task GraphStores_UpdateExistingNodes(string providerKey)
    {
        var store = GetStore(providerKey);
        if (store is null)
        {
            return;
        }
        await store.InitializeAsync();

        var label = ProviderLabels[providerKey];
        var nodeId = $"{providerKey}-update-{Guid.NewGuid():N}";

        await store.UpsertNodeAsync(nodeId, label, new Dictionary<string, object?> { ["name"] = "alpha", ["score"] = 1 });
        await store.UpsertNodeAsync(nodeId, label, new Dictionary<string, object?> { ["name"] = "beta", ["score"] = 2 });

        var node = await FindNodeAsync(store, nodeId);
        Assert.NotNull(node);
        Assert.Equal("beta", node!.Properties["name"]);
        Assert.Equal(2, Convert.ToInt32(node.Properties["score"], CultureInfo.InvariantCulture));
    }

    [Theory]
    [MemberData(nameof(GraphProviders))]
    public async Task GraphStores_RemovePropertiesWhenValueIsNull(string providerKey)
    {
        var store = GetStore(providerKey);
        if (store is null)
        {
            return;
        }
        await store.InitializeAsync();

        var label = ProviderLabels[providerKey];
        var nodeId = $"{providerKey}-cleanup-{Guid.NewGuid():N}";

        await store.UpsertNodeAsync(nodeId, label, new Dictionary<string, object?> { ["nickname"] = "alpha" });
        var node = await FindNodeAsync(store, nodeId);
        Assert.Equal("alpha", node!.Properties["nickname"]);

        await store.UpsertNodeAsync(nodeId, label, new Dictionary<string, object?> { ["nickname"] = null });
        var updated = await FindNodeAsync(store, nodeId);
        Assert.False(updated!.Properties.ContainsKey("nickname"));
    }

    [Theory]
    [MemberData(nameof(GraphProviders))]
    public async Task GraphStores_HandleBidirectionalRelationships(string providerKey)
    {
        var store = GetStore(providerKey);
        if (store is null)
        {
            return;
        }
        await store.InitializeAsync();

        var label = ProviderLabels[providerKey];
        var a = $"{providerKey}-bi-a-{Guid.NewGuid():N}";
        var b = $"{providerKey}-bi-b-{Guid.NewGuid():N}";

        await store.UpsertNodeAsync(a, label, new Dictionary<string, object?>());
        await store.UpsertNodeAsync(b, label, new Dictionary<string, object?>());

        var relationships = new[]
        {
            new GraphRelationshipUpsert(a, b, "KNOWS", new Dictionary<string, object?> { ["direction"] = "forward" }, Bidirectional: true)
        };

        await store.UpsertRelationshipsAsync(relationships);

        var outgoingA = await CollectAsync(store.GetOutgoingRelationshipsAsync(a));
        var outgoingB = await CollectAsync(store.GetOutgoingRelationshipsAsync(b));

        Assert.Contains(outgoingA, rel => rel.TargetId == b && rel.Type == "KNOWS");
        Assert.Contains(outgoingB, rel => rel.TargetId == a && rel.Type == "KNOWS");
    }

    [Theory]
    [MemberData(nameof(GraphProviders))]
    public async Task GraphStores_CanCreateAndRetrieveNodes(string providerKey)
    {
        var store = GetStore(providerKey);
        if (store is null)
        {
            return;
        }
        await store.InitializeAsync();

        var label = ProviderLabels[providerKey];
        var nodeId = $"{providerKey}-node-{Guid.NewGuid():N}";
        var props = new Dictionary<string, object?>
        {
            ["name"] = $"name-{providerKey}",
            ["index"] = 1
        };

        await store.UpsertNodeAsync(nodeId, label, props);
        var node = await FindNodeAsync(store, nodeId);
        Assert.NotNull(node);
        Assert.Equal(label, node!.Label);
        Assert.Equal($"name-{providerKey}", node.Properties["name"]);
    }

    [Theory]
    [MemberData(nameof(GraphProviders))]
    public async Task GraphStores_CanCreateAndRetrieveRelationships(string providerKey)
    {
        var store = GetStore(providerKey);
        if (store is null)
        {
            return;
        }
        await store.InitializeAsync();

        var label = ProviderLabels[providerKey];
        var sourceId = $"{providerKey}-rel-src-{Guid.NewGuid():N}";
        var targetId = $"{providerKey}-rel-dst-{Guid.NewGuid():N}";

        await store.UpsertNodeAsync(sourceId, label, new Dictionary<string, object?>());
        await store.UpsertNodeAsync(targetId, label, new Dictionary<string, object?>());
        await store.UpsertRelationshipAsync(sourceId, targetId, "CONNECTS", new Dictionary<string, object?>
        {
            ["score"] = 0.99,
            ["provider"] = providerKey
        });

        var outgoing = await CollectAsync(store.GetOutgoingRelationshipsAsync(sourceId));
        var relationship = Assert.Single(outgoing, rel => rel.TargetId == targetId);
        Assert.Equal("CONNECTS", relationship.Type);
        Assert.Equal(providerKey, relationship.Properties["provider"]);

        var allEdges = await CollectAsync(store.GetRelationshipsAsync());
        Assert.Contains(allEdges, rel => rel.SourceId == sourceId && rel.TargetId == targetId);
    }

    [Theory]
    [MemberData(nameof(GraphProviders))]
    public async Task GraphStores_CanUpsertInBatch(string providerKey)
    {
        var store = GetStore(providerKey);
        if (store is null)
        {
            return;
        }
        await store.InitializeAsync();
        var label = ProviderLabels[providerKey];

        var nodes = Enumerable.Range(0, 3)
            .Select(index => new GraphNodeUpsert(
                $"{providerKey}-batch-node-{index}-{Guid.NewGuid():N}",
                label,
                new Dictionary<string, object?> { ["index"] = index }))
            .ToList();

        await store.UpsertNodesAsync(nodes);

        foreach (var node in nodes)
        {
            Assert.NotNull(await FindNodeAsync(store, node.Id));
        }

        var relationships = nodes.Skip(1)
            .Select(node => new GraphRelationshipUpsert(nodes[0].Id, node.Id, "CONNECTS", new Dictionary<string, object?>()))
            .ToList();

        await store.UpsertRelationshipsAsync(relationships);
        var outgoing = await CollectAsync(store.GetOutgoingRelationshipsAsync(nodes[0].Id));
        Assert.Equal(relationships.Count, outgoing.Count);
    }

    [Theory]
    [MemberData(nameof(GraphProviders))]
    public async Task GraphStores_CanDeleteRelationshipsByRewriting(string providerKey)
    {
        var store = GetStore(providerKey);
        if (store is null)
        {
            return;
        }
        await store.InitializeAsync();

        var label = ProviderLabels[providerKey];
        var sourceId = $"{providerKey}-del-src-{Guid.NewGuid():N}";
        var targetId = $"{providerKey}-del-dst-{Guid.NewGuid():N}";

        await store.UpsertNodeAsync(sourceId, label, new Dictionary<string, object?>());
        await store.UpsertNodeAsync(targetId, label, new Dictionary<string, object?>());
        await store.UpsertRelationshipAsync(sourceId, targetId, "CONNECTS", new Dictionary<string, object?>());

        var initial = await CollectAsync(store.GetOutgoingRelationshipsAsync(sourceId));
        Assert.Contains(initial, rel => rel.TargetId == targetId);

        await store.UpsertRelationshipAsync(sourceId, targetId, "CONNECTS", new Dictionary<string, object?> { ["flag"] = "active" });
        var updated = await CollectAsync(store.GetOutgoingRelationshipsAsync(sourceId));

        Assert.Contains(updated, rel => rel.TargetId == targetId && rel.Properties.ContainsKey("flag"));
    }

    [Theory]
    [MemberData(nameof(GraphProviders))]
    public async Task GraphStores_HandlePagination(string providerKey)
    {
        var graphStore = GetStore(providerKey);
        if (graphStore is null)
        {
            return;
        }
        await graphStore.InitializeAsync();

        var label = ProviderLabels.GetValueOrDefault(providerKey, "Entity");
        var nodeIds = new List<string>();
        for (var i = 0; i < 5; i++)
        {
            var id = $"{providerKey}-page-node-{i}-{Guid.NewGuid():N}";
            nodeIds.Add(id);
            await graphStore.UpsertNodeAsync(id, label, new Dictionary<string, object?> { ["index"] = i });
        }

        var firstTwo = await CollectAsync(graphStore.GetNodesAsync(new GraphTraversalOptions { Take = 2 }));
        Assert.Equal(2, firstTwo.Count);

        var nextTwo = await CollectAsync(graphStore.GetNodesAsync(new GraphTraversalOptions { Skip = 2, Take = 2 }));
        Assert.Equal(2, nextTwo.Count);

        Assert.NotEqual(firstTwo.Select(n => n.Id), nextTwo.Select(n => n.Id));

        var sourceId = nodeIds[0];
        for (var i = 1; i < nodeIds.Count; i++)
        {
            await graphStore.UpsertRelationshipAsync(sourceId, nodeIds[i], "CONNECTS", new Dictionary<string, object?> { ["index"] = i });
        }

        var pagedEdges = await CollectAsync(graphStore.GetRelationshipsAsync(new GraphTraversalOptions { Take = 2 }));
        Assert.Equal(2, pagedEdges.Count);
    }

    [Fact]
    [Trait("Category", "Cosmos")]
    public async Task CosmosGraphStore_RoundTrips_WhenEmulatorAvailable()
    {
        var cosmosStore = fixture.Services.GetKeyedService<IGraphStore>("cosmos");
        if (cosmosStore is null)
        {
            return;
        }

        const string label = "Document";
        var sourceId = $"cosmos-src-{Guid.NewGuid():N}";
        var targetId = $"cosmos-dst-{Guid.NewGuid():N}";

        await cosmosStore.InitializeAsync();
        await cosmosStore.UpsertNodeAsync(sourceId, label, new Dictionary<string, object?> { ["title"] = "Source" });
        await cosmosStore.UpsertNodeAsync(targetId, label, new Dictionary<string, object?> { ["title"] = "Target" });
        await cosmosStore.UpsertRelationshipAsync(sourceId, targetId, "REFERENCES", new Dictionary<string, object?> { ["confidence"] = 0.5 });

        var relationships = new List<GraphRelationship>();
        await foreach (var edge in cosmosStore.GetOutgoingRelationshipsAsync(sourceId))
        {
            relationships.Add(edge);
        }

        Assert.Contains(relationships, rel => rel.TargetId == targetId && rel.Type == "REFERENCES");

        var nodeIds = new HashSet<string>();
        await foreach (var node in cosmosStore.GetNodesAsync())
        {
            nodeIds.Add(node.Id);
        }

        Assert.Contains(sourceId, nodeIds);
        Assert.Contains(targetId, nodeIds);

        var edges = new List<GraphRelationship>();
        await foreach (var edge in cosmosStore.GetRelationshipsAsync())
        {
            edges.Add(edge);
        }

        Assert.Contains(edges, rel => rel.SourceId == sourceId && rel.TargetId == targetId && rel.Type == "REFERENCES");
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

    private IGraphStore? GetStore(string providerKey) =>
        fixture.Services.GetKeyedService<IGraphStore>(providerKey);

    private static async Task<GraphNode?> FindNodeAsync(IGraphStore store, string nodeId, CancellationToken cancellationToken = default)
    {
        await foreach (var node in store.GetNodesAsync(cancellationToken: cancellationToken))
        {
            if (node.Id == nodeId)
            {
                return node;
            }
        }

        return null;
    }
}
