using GraphRag.Storage.Postgres;
using GraphRag.Storage.Postgres.ApacheAge;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Npgsql;

namespace ManagedCode.GraphRag.Tests.Integration;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class PostgresConcurrencyTests(GraphRagApplicationFixture fixture)
{
    private const string SeedNodeId = "__seed__";
    private const int SharedConnectionLimit = 40;
    private readonly GraphRagApplicationFixture _fixture = fixture;

    [Fact]
    public async Task AgeConnectionManager_HandlesConcurrentGraphWrites_WithSharedManager()
    {
        var connectionString = _fixture.PostgresConnectionString;
        var graphName = $"concurrency_{Guid.NewGuid():N}";

        await using var manager = CreateManager(connectionString, SharedConnectionLimit);
        await SeedGraphAsync(manager, graphName);

        var tasks = Enumerable.Range(0, SharedConnectionLimit)
            .Select(index => UpsertAndVerifyNodeAsync(manager, graphName, index));

        await Task.WhenAll(tasks);

        await AssertNodeCountAsync(manager, graphName, SharedConnectionLimit);
        await CleanupGraphAsync(manager, graphName);
    }

    [Fact]
    public async Task AgeConnectionManager_HandlesConcurrentGraphWrites_WithEphemeralManagers()
    {
        var connectionString = _fixture.PostgresConnectionString;
        var graphName = $"concurrency_{Guid.NewGuid():N}";

        await using var manager = CreateManager(connectionString, SharedConnectionLimit);
        await SeedGraphAsync(manager, graphName);

        var tasks = Enumerable.Range(0, 5000).Select(async index =>
        {
            await UpsertAndVerifyNodeAsync(manager, graphName, index).ConfigureAwait(false);
        });

        await Task.WhenAll(tasks);

        await AssertNodeCountAsync(manager, graphName, 5000);
        await CleanupGraphAsync(manager, graphName);
    }

    private static AgeConnectionManager CreateManager(string connectionString, int maxConnections = SharedConnectionLimit) =>
        new(ConfigurePool(connectionString, maxConnections), NullLogger<AgeConnectionManager>.Instance);

    [Fact]
    public async Task AgeClientFactory_CreatesManyClientsSequentially()
    {
        var connectionString = _fixture.PostgresConnectionString;
        var graphName = $"factory_{Guid.NewGuid():N}";

        var services = new ServiceCollection()
            .AddLogging()
            .AddPostgresGraphStore("factory", options =>
            {
                options.ConnectionString = ConfigurePool(connectionString, SharedConnectionLimit);
                options.GraphName = graphName;
            });

        await using var provider = services.BuildServiceProvider();

        var manager = provider.GetRequiredKeyedService<IAgeConnectionManager>("factory");
        await SeedGraphAsync(manager, graphName);

        var factory = provider.GetRequiredKeyedService<IAgeClientFactory>("factory");

        for (var i = 0; i < 1500; i++)
        {
            await using var client = factory.CreateClient();
            await client.OpenConnectionAsync();

            var exists = await client.GraphExistsAsync(graphName);
            Assert.True(exists, "Graph should exist for every constructed client.");

            await client.CloseConnectionAsync();
        }

        await CleanupGraphAsync(manager, graphName);
    }

    [Fact]
    public async Task AgeClientFactory_HandlesParallelClients()
    {
        var connectionString = _fixture.PostgresConnectionString;
        var graphName = $"factory_{Guid.NewGuid():N}";

        var services = new ServiceCollection()
            .AddLogging()
            .AddPostgresGraphStore("factory", options =>
            {
                options.ConnectionString = ConfigurePool(connectionString, SharedConnectionLimit);
                options.GraphName = graphName;
            });

        await using var provider = services.BuildServiceProvider();

        var manager = provider.GetRequiredKeyedService<IAgeConnectionManager>("factory");
        await SeedGraphAsync(manager, graphName);

        var factory = provider.GetRequiredKeyedService<IAgeClientFactory>("factory");

        var tasks = Enumerable.Range(0, 1500).Select(async index =>
        {
            var nodeId = $"parallel-{index:D4}";
            await using var client = factory.CreateClient();
            await client.OpenConnectionAsync();
            var createCypher = $"CREATE (:ParallelNode {{ id: '{nodeId}', idx: {index} }})";
            await client.ExecuteCypherAsync(graphName, createCypher);

            await using var verifyCommand = new NpgsqlCommand(
                $"SELECT COUNT(*) FROM ag_catalog.cypher('{graphName}', $$ MATCH (n:ParallelNode {{ id: '{nodeId}' }}) RETURN n $$) AS (result ag_catalog.agtype);",
                client.Connection);
            var exists = (long)(await verifyCommand.ExecuteScalarAsync() ?? 0L);
            Assert.Equal(1, exists);

            await client.CloseConnectionAsync();
        });

        await Task.WhenAll(tasks);

        await CleanupGraphAsync(manager, graphName);
    }

    private static async Task SeedGraphAsync(IAgeConnectionManager manager, string graphName)
    {
        await using var client = new AgeClient(manager, NullLogger<AgeClient>.Instance);
        await client.OpenConnectionAsync().ConfigureAwait(false);
        await client.CreateGraphAsync(graphName).ConfigureAwait(false);
        await client.ExecuteCypherAsync(
            graphName,
            $"CREATE (:ConcurrencyTest {{ id: '{SeedNodeId}', idx: -1 }})").ConfigureAwait(false);
        await client.CloseConnectionAsync().ConfigureAwait(false);
    }

    private static async Task CleanupGraphAsync(IAgeConnectionManager manager, string graphName)
    {
        await using var client = new AgeClient(manager, NullLogger<AgeClient>.Instance);
        await client.OpenConnectionAsync().ConfigureAwait(false);
        await client.DropGraphAsync(graphName, cascade: true).ConfigureAwait(false);
        await client.CloseConnectionAsync().ConfigureAwait(false);
    }

    private static async Task UpsertAndVerifyNodeAsync(IAgeConnectionManager manager, string graphName, int index)
    {
        var nodeId = $"node-{index:D4}";

        await using var client = new AgeClient(manager, NullLogger<AgeClient>.Instance);
        await client.OpenConnectionAsync().ConfigureAwait(false);

        var createCypher = $"CREATE (:ConcurrencyTest {{ id: '{nodeId}', idx: {index} }})";
        await client.ExecuteCypherAsync(graphName, createCypher).ConfigureAwait(false);

        await using var verifyCommand = new NpgsqlCommand(
            $"SELECT COUNT(*) FROM ag_catalog.cypher('{graphName}', $$ MATCH (n:ConcurrencyTest {{ id: '{nodeId}' }}) RETURN n $$) AS (result ag_catalog.agtype);",
            client.Connection);
        var count = (long)(await verifyCommand.ExecuteScalarAsync().ConfigureAwait(false) ?? 0L);
        Assert.Equal(1, count);

        await client.CloseConnectionAsync().ConfigureAwait(false);
    }

    private static async Task AssertNodeCountAsync(IAgeConnectionManager manager, string graphName, int expected)
    {
        await using var client = new AgeClient(manager, NullLogger<AgeClient>.Instance);
        await client.OpenConnectionAsync().ConfigureAwait(false);

        await client.ExecuteCypherAsync(
            graphName,
            $"MATCH (n:ConcurrencyTest {{ id: '{SeedNodeId}' }}) DETACH DELETE n").ConfigureAwait(false);

        await using var countCommand = new NpgsqlCommand(
            $"SELECT COUNT(*) FROM ag_catalog.cypher('{graphName}', $$ MATCH (n:ConcurrencyTest) RETURN n $$) AS (result ag_catalog.agtype);",
            client.Connection);

        var inserted = (long)(await countCommand.ExecuteScalarAsync().ConfigureAwait(false) ?? 0L);
        Assert.Equal(expected, inserted);

        await client.CloseConnectionAsync().ConfigureAwait(false);
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
}
