using GraphRag.Graphs;
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

    [Fact]
    public async Task AgeClientFactory_ReusesConnectionsWithinScope()
    {
        var connectionString = _fixture.PostgresConnectionString;
        var graphName = $"scope_{Guid.NewGuid():N}";

        var services = new ServiceCollection()
            .AddLogging()
            .AddPostgresGraphStore("scope", options =>
            {
                options.ConnectionString = ConfigurePool(connectionString, 5);
                options.GraphName = graphName;
            });

        await using var provider = services.BuildServiceProvider();

        var manager = provider.GetRequiredKeyedService<IAgeConnectionManager>("scope");
        await SeedGraphAsync(manager, graphName);

        var factory = provider.GetRequiredKeyedService<IAgeClientFactory>("scope");

        await using var scope = await factory.CreateScopeAsync();

        long firstProcessId;
        await using (var firstClient = factory.CreateClient())
        {
            await firstClient.OpenConnectionAsync();
            firstProcessId = firstClient.Connection.ProcessID;
            await firstClient.CloseConnectionAsync();
        }

        await using var secondClient = factory.CreateClient();
        await secondClient.OpenConnectionAsync();
        var secondProcessId = secondClient.Connection.ProcessID;

        Assert.Equal(firstProcessId, secondProcessId);

        await secondClient.CloseConnectionAsync();

        await CleanupGraphAsync(manager, graphName);
    }

    [Fact]
    public async Task GraphStoreScopes_HandleMassiveParallelism()
    {
        var connectionString = _fixture.PostgresConnectionString;
        var graphName = $"scoped_load_{Guid.NewGuid():N}";

        var services = new ServiceCollection()
            .AddLogging()
            .AddPostgresGraphStore("scoped", options =>
            {
                options.ConnectionString = ConfigurePool(connectionString, 5);
                options.GraphName = graphName;
            });

        await using var provider = services.BuildServiceProvider();
        var store = provider.GetRequiredKeyedService<PostgresGraphStore>("scoped");
        await store.InitializeAsync();

        var scopedStore = Assert.IsAssignableFrom<IScopedGraphStore>(store);
        var manager = provider.GetRequiredKeyedService<IAgeConnectionManager>("scoped");

        const int scopeCount = 100;
        const int operationsPerScope = 500;
        var tasks = Enumerable.Range(0, scopeCount).Select(ExecuteScopeAsync);

        await Task.WhenAll(tasks);

        var totalNodes = await CountNodesAsync(manager, graphName, "ScopedLoadTest");
        Assert.Equal(scopeCount * operationsPerScope, totalNodes);

        await CleanupGraphAsync(manager, graphName);

        async Task ExecuteScopeAsync(int scopeIndex)
        {
            await using var scope = await scopedStore.CreateScopeAsync();
            for (var i = 0; i < operationsPerScope; i++)
            {
                var nodeId = $"scope-{scopeIndex:D4}-node-{i:D4}";
                var properties = new Dictionary<string, object?>
                {
                    ["scope"] = scopeIndex,
                    ["sequence"] = i
                };

                await store.UpsertNodeAsync(nodeId, "ScopedLoadTest", properties);
            }
        }
    }

    [Fact]
    public async Task AgeConnectionManager_RetriesWhenServerReportsTooManyClients()
    {
        var connectionString = _fixture.PostgresConnectionString;
        var heldConnections = new List<NpgsqlConnection>();

        try
        {
            const int maxAttempts = 256;
            var saturated = await TrySaturateServerConnectionsAsync(connectionString, maxAttempts, heldConnections);
            if (!saturated)
            {
                return;
            }

            await using var manager = CreateManager(connectionString, SharedConnectionLimit);
            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));

            var openTask = manager.OpenConnectionAsync(cts.Token);

            await Task.Delay(TimeSpan.FromMilliseconds(500));
            await ReleaseOneConnectionAsync(heldConnections);

            await using var connection = await openTask;
            Assert.True(connection.FullState.HasFlag(System.Data.ConnectionState.Open));

            await manager.ReturnConnectionAsync(connection, cts.Token);
        }
        finally
        {
            foreach (var connection in heldConnections)
            {
                await connection.DisposeAsync();
            }
        }
    }

    [Fact]
    public async Task AgeConnectionManager_ThrowsAfterRetryLimitWhenConnectionsUnavailable()
    {
        var connectionString = _fixture.PostgresConnectionString;
        var heldConnections = new List<NpgsqlConnection>();

        try
        {
            var saturated = await TrySaturateServerConnectionsAsync(connectionString, maxAttempts: 256, heldConnections);
            if (!saturated)
            {
                return;
            }

            await using var manager = CreateManager(connectionString, SharedConnectionLimit);
            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));

            await Assert.ThrowsAsync<PostgresException>(() => manager.OpenConnectionAsync(cts.Token));
        }
        finally
        {
            foreach (var connection in heldConnections)
            {
                await connection.DisposeAsync();
            }
        }
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

    private static async Task<long> CountNodesAsync(IAgeConnectionManager manager, string graphName, string label)
    {
        await using var client = new AgeClient(manager, NullLogger<AgeClient>.Instance);
        await client.OpenConnectionAsync().ConfigureAwait(false);

        await using var command = client.Connection.CreateCommand();
        command.CommandText = string.Concat(
            "SELECT COUNT(*) FROM ag_catalog.cypher('", graphName, "', $$ MATCH (n:", label, ") RETURN n $$) AS (result ag_catalog.agtype);");

        var count = (long)(await command.ExecuteScalarAsync().ConfigureAwait(false) ?? 0L);

        await client.CloseConnectionAsync().ConfigureAwait(false);
        return count;
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

    private static async Task<bool> TrySaturateServerConnectionsAsync(string connectionString, int maxAttempts, List<NpgsqlConnection> heldConnections)
    {
        for (var i = 0; i < maxAttempts; i++)
        {
            var connection = new NpgsqlConnection(connectionString);
            try
            {
                await connection.OpenAsync();
                heldConnections.Add(connection);
            }
            catch (PostgresException ex) when (ex.SqlState == PostgresErrorCodes.TooManyConnections)
            {
                await connection.DisposeAsync();
                return true;
            }
        }

        return false;
    }

    private static async Task ReleaseOneConnectionAsync(List<NpgsqlConnection> heldConnections)
    {
        if (heldConnections.Count == 0)
        {
            return;
        }

        var lastIndex = heldConnections.Count - 1;
        var connection = heldConnections[lastIndex];
        heldConnections.RemoveAt(lastIndex);
        await connection.DisposeAsync();
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
