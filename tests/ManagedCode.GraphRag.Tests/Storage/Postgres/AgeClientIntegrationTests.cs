using GraphRag.Storage.Postgres.ApacheAge;
using GraphRag.Storage.Postgres.ApacheAge.Types;
using ManagedCode.GraphRag.Tests.Integration;
using Microsoft.Extensions.Logging.Abstractions;

namespace ManagedCode.GraphRag.Tests.Storage.Postgres;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class AgeClientIntegrationTests(GraphRagApplicationFixture fixture)
{
    [Fact]
    public async Task AgeClient_RoundTripsVerticesWithAgtypeReader()
    {
        var connectionString = fixture.PostgresConnectionString;
        await using var manager = new AgeConnectionManager(connectionString, NullLogger<AgeConnectionManager>.Instance);
        await using var client = new AgeClient(manager, NullLogger<AgeClient>.Instance);

        await client.OpenConnectionAsync();
        var graphName = $"agetype_{Guid.NewGuid():N}";
        await client.CreateGraphAsync(graphName);
        var nodeId = $"node-{Guid.NewGuid():N}";

        await client.ExecuteCypherAsync(
            graphName,
            $"CREATE (:Entity {{ id: '{nodeId}', score: 42 }})");

        var query = $"SELECT * FROM ag_catalog.cypher('{graphName}', $$ MATCH (n:Entity {{ id: '{nodeId}' }}) RETURN n $$) AS (vertex ag_catalog.agtype);";
        var reader = await client.ExecuteQueryAsync(query);
        Assert.True(await reader.ReadAsync());

        var buffer = new object[reader.FieldCount];
        reader.GetValues(buffer);

        var directAgtype = (Agtype)buffer[0];
        var vertex = directAgtype.GetVertex();
        Assert.Equal(nodeId, vertex.Properties["id"]);

        var viaTyped = reader.GetValue<Agtype>(0);
        Assert.Equal(vertex.Label, viaTyped.GetVertex().Label);

        var viaAsync = await reader.GetValueAsync<Agtype>(0);
        Assert.Equal(vertex.Properties["score"], viaAsync.GetVertex().Properties["score"]);

        await reader.DisposeAsync();

        await client.DropGraphAsync(graphName, cascade: true);
        Assert.False(await client.GraphExistsAsync(graphName));
        await client.CloseConnectionAsync();
    }
}
