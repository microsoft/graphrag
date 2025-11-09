using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Integration;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class GraphStoreIntegrationTests(GraphRagApplicationFixture fixture)
{
    private static readonly IReadOnlyDictionary<string, string> ProviderLabels = new Dictionary<string, string>
    {
        ["neo4j"] = "Person",
        ["postgres"] = "Chapter"
    };

    public static IEnumerable<object[]> GraphProviders => ProviderLabels.Keys.Select(key => new object[] { key });

    [Theory]
    [MemberData(nameof(GraphProviders))]
    public async Task GraphStores_RoundTripRelationshipsAsync(string providerKey)
    {
        var graphStore = fixture.Services.GetRequiredKeyedService<IGraphStore>(providerKey);
        await graphStore.InitializeAsync();

        var sourceId = $"{providerKey}-src-{Guid.NewGuid():N}";
        var targetId = $"{providerKey}-dst-{Guid.NewGuid():N}";
        var relationType = "CONNECTS";
        var sourceProps = new Dictionary<string, object?>
        {
            ["name"] = $"{providerKey}-source"
        };
        var targetProps = new Dictionary<string, object?>
        {
            ["name"] = $"{providerKey}-target"
        };
        var edgeProps = new Dictionary<string, object?>
        {
            ["weight"] = 0.9,
            ["provider"] = providerKey
        };

        var label = ProviderLabels[providerKey];
        await graphStore.UpsertNodeAsync(sourceId, label, sourceProps);
        await graphStore.UpsertNodeAsync(targetId, label, targetProps);
        await graphStore.UpsertRelationshipAsync(sourceId, targetId, relationType, edgeProps);

        var relationships = new List<GraphRelationship>();
        await foreach (var relationship in graphStore.GetOutgoingRelationshipsAsync(sourceId))
        {
            relationships.Add(relationship);
        }

        var match = Assert.Single(relationships, rel => rel.TargetId == targetId);
        Assert.Equal(sourceId, match.SourceId);
        Assert.Equal(relationType, match.Type);
        Assert.Equal(providerKey, match.Properties["provider"]);

        var nodeIds = new HashSet<string>();
        await foreach (var node in graphStore.GetNodesAsync())
        {
            nodeIds.Add(node.Id);
        }

        Assert.Contains(sourceId, nodeIds);
        Assert.Contains(targetId, nodeIds);

        var edges = new List<GraphRelationship>();
        await foreach (var edge in graphStore.GetRelationshipsAsync())
        {
            edges.Add(edge);
        }

        Assert.Contains(edges, rel => rel.SourceId == sourceId && rel.TargetId == targetId && rel.Type == relationType);
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
}
