using GraphRag.Storage.Postgres.ApacheAge;
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
        new(connectionString, NullLogger<AgeConnectionManager>.Instance, maxConnections);

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
}
