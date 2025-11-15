using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Integration;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class GraphStoreStressTests(GraphRagApplicationFixture fixture)
{
    private const int ParallelOperations = 1500;

    private static readonly (string Key, string Label)[] ProviderMap =
    {
        ("postgres", "Chapter"),
        ("neo4j", "Person"),
        ("cosmos", "Document")
    };

    public static IEnumerable<object[]> Providers => ProviderMap.Select(tuple => new object[] { tuple.Key, tuple.Label });

    [Theory]
    [MemberData(nameof(Providers))]
    public async Task GraphStores_HandleParallelMutationsAsync(string providerKey, string label)
    {
        var graphStore = fixture.Services.GetKeyedService<IGraphStore>(providerKey);
        if (graphStore is null)
        {
            return;
        }

        await graphStore.InitializeAsync();
        var rootId = $"{providerKey}-root-{Guid.NewGuid():N}";
        await graphStore.UpsertNodeAsync(rootId, label, new Dictionary<string, object?> { ["name"] = "root" });

        var prefix = $"{providerKey}-stress-{Guid.NewGuid():N}";
        var warmupId = $"{prefix}-priming";
        await graphStore.UpsertNodeAsync(warmupId, label, new Dictionary<string, object?> { ["provider"] = providerKey, ["primed"] = true });
        await graphStore.UpsertRelationshipAsync(rootId, warmupId, "STRESS_LINK", new Dictionary<string, object?> { ["weight"] = -1 });

        var tasks = Enumerable.Range(0, ParallelOperations)
            .Select(index => ExecuteMutationAsync(graphStore, rootId, label, prefix, providerKey, index));

        await Task.WhenAll(tasks);

        await AssertNodesWithPrefixAsync(graphStore, prefix, ParallelOperations, warmupId);
        await AssertRelationshipsFromRootAsync(graphStore, rootId, prefix, ParallelOperations, warmupId);
    }

    private static async Task ExecuteMutationAsync(IGraphStore graphStore, string rootId, string label, string prefix, string providerKey, int index)
    {
        var nodeId = $"{prefix}-{index:D4}";
        var nodeProps = new Dictionary<string, object?>
        {
            ["provider"] = providerKey,
            ["index"] = index
        };

        await graphStore.UpsertNodeAsync(nodeId, label, nodeProps);

        var relationshipProps = new Dictionary<string, object?>
        {
            ["weight"] = index
        };

        await graphStore.UpsertRelationshipAsync(rootId, nodeId, "STRESS_LINK", relationshipProps);

        await foreach (var relationship in graphStore.GetOutgoingRelationshipsAsync(nodeId))
        {
            if (relationship.SourceId == nodeId)
            {
                break;
            }
        }
    }

    private static async Task AssertNodesWithPrefixAsync(IGraphStore graphStore, string prefix, int expectedCount, params string[] excluded)
    {
        var nodes = new HashSet<string>(StringComparer.Ordinal);
        await foreach (var node in graphStore.GetNodesAsync())
        {
            if (node.Id.StartsWith(prefix, StringComparison.Ordinal))
            {
                nodes.Add(node.Id);
            }
        }

        nodes.ExceptWith(excluded);
        Assert.Equal(expectedCount, nodes.Count);
    }

    private static async Task AssertRelationshipsFromRootAsync(IGraphStore graphStore, string rootId, string prefix, int expectedCount, params string[] excluded)
    {
        var relationships = new HashSet<string>(StringComparer.Ordinal);
        await foreach (var relationship in graphStore.GetRelationshipsAsync())
        {
            if (relationship.SourceId == rootId && relationship.TargetId.StartsWith(prefix, StringComparison.Ordinal))
            {
                relationships.Add(relationship.TargetId);
            }
        }

        relationships.ExceptWith(excluded);
        Assert.Equal(expectedCount, relationships.Count);
    }
}
