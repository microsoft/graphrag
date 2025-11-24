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
