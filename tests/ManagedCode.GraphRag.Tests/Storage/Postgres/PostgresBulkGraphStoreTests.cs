using GraphRag.Graphs;
using GraphRag.Storage.Postgres;
using GraphRag.Storage.Postgres.ApacheAge;
using ManagedCode.GraphRag.Tests.Integration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Npgsql;

namespace ManagedCode.GraphRag.Tests.Storage.Postgres;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class PostgresBulkGraphStoreTests(GraphRagApplicationFixture fixture)
{
    private readonly GraphRagApplicationFixture _fixture = fixture;

    [Fact]
    public async Task BulkUpserts_InsertNodesAndRelationships()
    {
        var connectionString = _fixture.PostgresConnectionString;
        var graphName = $"bulk_{Guid.NewGuid():N}";

        var services = new ServiceCollection()
            .AddLogging()
            .AddPostgresGraphStore("bulk", options =>
            {
                options.ConnectionString = connectionString;
                options.GraphName = graphName;
            });

        await using var provider = services.BuildServiceProvider();
        var store = provider.GetRequiredKeyedService<PostgresGraphStore>("bulk");
        var connectionManager = provider.GetRequiredKeyedService<IAgeConnectionManager>("bulk");
        var clientFactory = provider.GetRequiredKeyedService<IAgeClientFactory>("bulk");
        await store.InitializeAsync();

        await using var scope = await clientFactory.CreateScopeAsync();

        var bulkStore = provider.GetRequiredKeyedService<IGraphStore>("bulk");
        await bulkStore.UpsertNodesAsync(new[]
        {
            new GraphNodeUpsert("bulk-node-1", "BulkEntity", new Dictionary<string, object?> { ["name"] = "first" }),
            new GraphNodeUpsert("bulk-node-2", "BulkEntity", new Dictionary<string, object?> { ["name"] = "second" }),
            new GraphNodeUpsert("bulk-node-3", "BulkOther", new Dictionary<string, object?> { ["name"] = "third" })
        });

        await bulkStore.UpsertRelationshipsAsync(new[]
        {
            new GraphRelationshipUpsert("bulk-node-1", "bulk-node-2", "RELATES_TO", new Dictionary<string, object?> { ["weight"] = 0.5 }),
            new GraphRelationshipUpsert("bulk-node-2", "bulk-node-3", "RELATES_TO", new Dictionary<string, object?> { ["weight"] = 0.8 }, Bidirectional: true)
        });

        var nodes = new List<GraphNode>();
        await foreach (var node in store.GetNodesAsync(cancellationToken: CancellationToken.None))
        {
            nodes.Add(node);
        }

        Assert.Equal(3, nodes.Count);

        var relationships = new List<GraphRelationship>();
        await foreach (var relationship in store.GetRelationshipsAsync(cancellationToken: CancellationToken.None))
        {
            relationships.Add(relationship);
        }

        Assert.Equal(3, relationships.Count);

        await CleanupGraphAsync(connectionManager, graphName);
    }

    [Fact]
    public async Task BulkUpserts_WorkWithinScopedConnection()
    {
        var connectionString = ConfigurePool(_fixture.PostgresConnectionString, maxConnections: 4);
        var graphName = $"bulk_scope_{Guid.NewGuid():N}";

        var services = new ServiceCollection()
            .AddLogging()
            .AddPostgresGraphStore("bulk_scope", options =>
            {
                options.ConnectionString = connectionString;
                options.GraphName = graphName;
            });

        await using var provider = services.BuildServiceProvider();
        var store = provider.GetRequiredKeyedService<PostgresGraphStore>("bulk_scope");
        var connectionManager = provider.GetRequiredKeyedService<IAgeConnectionManager>("bulk_scope");
        var clientFactory = provider.GetRequiredKeyedService<IAgeClientFactory>("bulk_scope");
        await store.InitializeAsync();

        var bulkStore = provider.GetRequiredKeyedService<IGraphStore>("bulk_scope");

        await using (await clientFactory.CreateScopeAsync())
        {
            await bulkStore.UpsertNodesAsync(new[]
            {
                new GraphNodeUpsert("scoped-node-1", "ScopedBulk", new Dictionary<string, object?> { ["name"] = "first" }),
                new GraphNodeUpsert("scoped-node-2", "ScopedBulk", new Dictionary<string, object?> { ["name"] = "second" })
            });

            await bulkStore.UpsertRelationshipsAsync(new[]
            {
                new GraphRelationshipUpsert("scoped-node-1", "scoped-node-2", "RELATES_TO", new Dictionary<string, object?>())
            });
        }

        var nodes = new List<GraphNode>();
        await foreach (var node in store.GetNodesAsync(cancellationToken: CancellationToken.None))
        {
            nodes.Add(node);
        }

        Assert.Equal(2, nodes.Count);

        await CleanupGraphAsync(connectionManager, graphName);
    }

    private static string ConfigurePool(string connectionString, int maxConnections)
    {
        var builder = new NpgsqlConnectionStringBuilder(connectionString)
        {
            MaxPoolSize = maxConnections,
            MinPoolSize = Math.Min(10, maxConnections)
        };

        return builder.ConnectionString;
    }

    private static async Task CleanupGraphAsync(IAgeConnectionManager manager, string graphName)
    {
        await using var client = new AgeClient(manager, NullLogger<AgeClient>.Instance);
        await client.OpenConnectionAsync();
        await client.DropGraphAsync(graphName, cascade: true);
        await client.CloseConnectionAsync();
    }
}
