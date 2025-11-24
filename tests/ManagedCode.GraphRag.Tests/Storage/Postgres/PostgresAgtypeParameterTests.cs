using System.Globalization;
using System.Text.Json;
using GraphRag.Constants;
using GraphRag.Graphs;
using GraphRag.Storage.Postgres.ApacheAge;
using GraphRag.Storage.Postgres.ApacheAge.Types;
using ManagedCode.GraphRag.Tests.Integration;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.DependencyInjection;
using Npgsql;

namespace ManagedCode.GraphRag.Tests.Storage.Postgres;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class PostgresAgtypeParameterTests(GraphRagApplicationFixture fixture)
{
    private readonly GraphRagApplicationFixture _fixture = fixture;

    [Fact]
    public async Task CypherParameters_WithStringValues_AreWrittenAsAgtype()
    {
        var connectionString = _fixture.PostgresConnectionString;
        await using var manager = new AgeConnectionManager(connectionString, NullLogger<AgeConnectionManager>.Instance);
        await using var client = new AgeClient(manager, NullLogger<AgeClient>.Instance);

        await client.OpenConnectionAsync();
        var graphName = $"params_{Guid.NewGuid():N}";
        var nodeId = $"node-{Guid.NewGuid():N}";

        try
        {
            await client.CreateGraphAsync(graphName);

            var cypherParams = new Dictionary<string, object?>
            {
                [CypherParameterNames.NodeId] = nodeId,
                ["name"] = "mentor-string",
                ["bio"] = "Line one\nLine two"
            };

            var payload = JsonSerializer.Serialize(cypherParams);

            await using (var command = client.Connection.CreateCommand())
            {
                command.AllResultTypesAreUnknown = true;
                command.CommandText = string.Concat(
                    "SELECT * FROM ag_catalog.cypher('", graphName, "', $$",
                    "\n    CREATE (:Person { id: $", CypherParameterNames.NodeId, ", name: $name, bio: $bio })",
                    "\n$$, @", CypherParameterNames.Parameters, "::ag_catalog.agtype) AS (result agtype);");

                command.Parameters.Add(new NpgsqlParameter<Agtype>(CypherParameterNames.Parameters, new Agtype(payload))
                {
                    DataTypeName = "ag_catalog.agtype"
                });

                await command.ExecuteNonQueryAsync();
            }

            await using var verify = client.Connection.CreateCommand();
            verify.AllResultTypesAreUnknown = true;
            verify.CommandText = string.Concat(
                "SELECT * FROM ag_catalog.cypher('", graphName, "', $$",
                "\n    MATCH (n:Person { id: '", nodeId, "' }) RETURN n",
                "\n$$) AS (vertex ag_catalog.agtype);");

            var result = await verify.ExecuteScalarAsync();
            var agResult = new Agtype(Convert.ToString(result, CultureInfo.InvariantCulture) ?? string.Empty);
            var vertex = agResult.GetVertex();

            Assert.Equal(nodeId, vertex.Properties["id"]);
            Assert.Equal("mentor-string", vertex.Properties["name"]);
            Assert.Equal("Line one\nLine two", vertex.Properties["bio"]);
        }
        finally
        {
            await client.DropGraphAsync(graphName, cascade: true);
            await client.CloseConnectionAsync();
        }
    }

    [Fact]
    public async Task GraphStore_UpsertNodes_WithStringProperties_UsesAgtypeParameters()
    {
        var store = _fixture.Services.GetKeyedService<IGraphStore>("postgres");
        Assert.NotNull(store);

        await store!.InitializeAsync();

        var label = GraphStoreTestProviders.GetLabel("postgres");
        var nodeId = $"postgres-agparam-{Guid.NewGuid():N}";
        var description = "Line1\nLine2 \"quoted\" with braces { }";

        var nodes = new[]
        {
            new GraphNodeUpsert(
                nodeId,
                label,
                new Dictionary<string, object?>
                {
                    ["description"] = description,
                    ["category"] = "mentorship"
                })
        };

        await store.UpsertNodesAsync(nodes);

        var stored = await FindNodeAsync(store, nodeId);
        Assert.NotNull(stored);
        Assert.Equal(description, stored!.Properties["description"]?.ToString());
        Assert.Equal("mentorship", stored.Properties["category"]?.ToString());
    }

    [Fact]
    public async Task GraphStore_RejectsInjectionAttempts_InPropertyValues()
    {
        var store = _fixture.Services.GetKeyedService<IGraphStore>("postgres");
        Assert.NotNull(store);
        await store!.InitializeAsync();

        var label = GraphStoreTestProviders.GetLabel("postgres");
        var sentinelId = $"postgres-sentinel-{Guid.NewGuid():N}";
        var attackerId = $"postgres-inject-{Guid.NewGuid():N}";

        // Baseline node that must survive any attempted injection.
        await store.UpsertNodeAsync(sentinelId, label, new Dictionary<string, object?> { ["name"] = "sentinel" });

        var injectionPayload = "alice'); MATCH (n) DETACH DELETE n; //";

        await store.UpsertNodeAsync(attackerId, label, new Dictionary<string, object?>
        {
            ["name"] = injectionPayload,
            ["role"] = "attacker"
        });

        var nodes = await CollectAsync(store.GetNodesAsync());
        Assert.Contains(nodes, n => n.Id == sentinelId && n.Properties["name"]?.ToString() == "sentinel");
        var injected = Assert.Single(nodes, n => n.Id == attackerId);
        Assert.Equal(injectionPayload, injected.Properties["name"]?.ToString());
        Assert.Equal("attacker", injected.Properties["role"]?.ToString());
    }

    [Fact]
    public async Task GraphStore_RejectsInjectionAttempts_InIds()
    {
        var store = _fixture.Services.GetKeyedService<IGraphStore>("postgres");
        Assert.NotNull(store);
        await store!.InitializeAsync();

        var label = GraphStoreTestProviders.GetLabel("postgres");
        var safeId = $"postgres-safe-{Guid.NewGuid():N}";
        var dangerousId = $"danger-') RETURN 1 //";

        await store.UpsertNodeAsync(safeId, label, new Dictionary<string, object?> { ["flag"] = "safe" });
        await store.UpsertNodeAsync(dangerousId, label, new Dictionary<string, object?> { ["flag"] = "danger" });

        var nodes = await CollectAsync(store.GetNodesAsync());
        Assert.Contains(nodes, n => n.Id == safeId && n.Properties["flag"]?.ToString() == "safe");
        Assert.Contains(nodes, n => n.Id == dangerousId && n.Properties["flag"]?.ToString() == "danger");
    }

    [Fact]
    public async Task DeleteNodes_DoesNotCascade_WhenIdsContainInjectionLikeContent()
    {
        var store = _fixture.Services.GetKeyedService<IGraphStore>("postgres");
        Assert.NotNull(store);
        await store!.InitializeAsync();

        var label = GraphStoreTestProviders.GetLabel("postgres");
        var sentinelId = $"postgres-safe-{Guid.NewGuid():N}";
        var attackerId = "kill-all-nodes\") DETACH DELETE n //";

        await store.UpsertNodeAsync(sentinelId, label, new Dictionary<string, object?> { ["flag"] = "safe" });
        await store.UpsertNodeAsync(attackerId, label, new Dictionary<string, object?> { ["flag"] = "danger" });

        await store.DeleteNodesAsync(new[] { attackerId });

        var nodes = await CollectAsync(store.GetNodesAsync());
        Assert.Contains(nodes, n => n.Id == sentinelId && n.Properties["flag"]?.ToString() == "safe");
        Assert.DoesNotContain(nodes, n => n.Id == attackerId);
    }

    [Fact]
    public async Task UpsertNode_ThrowsOnInvalidLabelCharacters()
    {
        var store = _fixture.Services.GetKeyedService<IGraphStore>("postgres");
        Assert.NotNull(store);

        var badLabel = "User) DETACH DELETE n";
        await Assert.ThrowsAsync<ArgumentException>(async () =>
            await store!.UpsertNodeAsync("id", badLabel, new Dictionary<string, object?>()));
    }

    public static IEnumerable<object[]> InjectionStringPayloads => new[]
    {
        new object[] { "'; DROP SCHEMA public; --" },
        new object[] { "$$; SELECT 1; $$" },
        new object[] { "\") MATCH (n) DETACH DELETE n //" },
        new object[] { "alice\n); RETURN 1; //" },
        new object[] { "\"quoted\" with {{braces}} and ;" },
        new object[] { "unicode-rtl-\u202Epayload" }
    };

    [Theory]
    [MemberData(nameof(InjectionStringPayloads))]
    public async Task GraphStore_RejectsInjectionAttempts_InProperties_WithVariousPayloads(string payload)
    {
        var store = _fixture.Services.GetKeyedService<IGraphStore>("postgres");
        Assert.NotNull(store);
        await store!.InitializeAsync();

        var label = GraphStoreTestProviders.GetLabel("postgres");
        var sentinelId = $"postgres-sentinel-{Guid.NewGuid():N}";
        var attackerId = $"postgres-inject-{Guid.NewGuid():N}";

        await store.UpsertNodeAsync(sentinelId, label, new Dictionary<string, object?> { ["name"] = "sentinel" });
        await store.UpsertNodeAsync(attackerId, label, new Dictionary<string, object?> { ["payload"] = payload });

        var nodes = await CollectAsync(store.GetNodesAsync());
        Assert.Contains(nodes, n => n.Id == sentinelId && n.Properties["name"]?.ToString() == "sentinel");
        var injected = Assert.Single(nodes, n => n.Id == attackerId);
        Assert.Equal(payload, injected.Properties["payload"]?.ToString());
    }

    [Fact]
    public async Task GraphStore_RejectsInjectionAttempts_InRelationshipTypes()
    {
        var store = _fixture.Services.GetKeyedService<IGraphStore>("postgres");
        Assert.NotNull(store);
        await store!.InitializeAsync();

        var label = GraphStoreTestProviders.GetLabel("postgres");
        var src = $"postgres-rel-{Guid.NewGuid():N}";
        var dst = $"postgres-rel-{Guid.NewGuid():N}";
        await store!.UpsertNodeAsync(src, label, new Dictionary<string, object?>());
        await store.UpsertNodeAsync(dst, label, new Dictionary<string, object?>());

        var badType = "BADTYPE'); MATCH (n) DETACH DELETE n; //";
        await Assert.ThrowsAsync<ArgumentException>(async () =>
            await store.UpsertRelationshipAsync(src, dst, badType, new Dictionary<string, object?> { ["score"] = 1 }));
    }

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

    private static async Task<List<GraphNode>> CollectAsync(IAsyncEnumerable<GraphNode> source)
    {
        var list = new List<GraphNode>();
        await foreach (var item in source)
        {
            list.Add(item);
        }

        return list;
    }
}
