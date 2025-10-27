using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using GraphRag.Graphs;
using GraphRag.Storage.Postgres;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Npgsql;
using NpgsqlTypes;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Integration;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class PostgresGraphStoreIntegrationTests
{
    private readonly GraphRagApplicationFixture _fixture;

    public PostgresGraphStoreIntegrationTests(GraphRagApplicationFixture fixture)
    {
        _fixture = fixture;
    }

    [Fact]
    public async Task UpsertNode_NormalizesNestedProperties()
    {
        var store = _fixture.Services.GetRequiredKeyedService<PostgresGraphStore>("postgres");
        await store.InitializeAsync();

        var nodeId = $"entity-{Guid.NewGuid():N}";
        var properties = new Dictionary<string, object?>
        {
            ["intValue"] = 1,
            ["boolValue"] = true,
            ["array"] = new object?[] { "alpha", 2, false },
            ["objectValue"] = new Dictionary<string, object?> { ["inner"] = "value" },
            ["bytes"] = Encoding.UTF8.GetBytes("abc"),
            ["timestamp"] = new DateTime(2024, 1, 1, 8, 30, 0, DateTimeKind.Local),
            ["id"] = "should-be-ignored"
        };

        using var json = JsonDocument.Parse("{\"name\":\"GraphRAG\",\"count\":5}");
        properties["json"] = json.RootElement.Clone();

        await store.UpsertNodeAsync(nodeId, "Entity", properties);

        var payload = await GetNodePropertiesAsync(_fixture.PostgresConnectionString, nodeId);

        Assert.Equal(nodeId, payload.GetProperty("id").GetString());
        Assert.Equal(1L, payload.GetProperty("intValue").GetInt64());
        Assert.True(payload.GetProperty("boolValue").GetBoolean());

        var array = payload.GetProperty("array").EnumerateArray().ToList();
        Assert.Equal("alpha", array[0].GetString());
        Assert.Equal(2L, array[1].GetInt64());
        Assert.False(array[2].GetBoolean());

        var nested = payload.GetProperty("objectValue");
        Assert.Equal("value", nested.GetProperty("inner").GetString());

        Assert.Equal(Convert.ToBase64String(Encoding.UTF8.GetBytes("abc")), payload.GetProperty("bytes").GetString());

        var jsonProp = payload.GetProperty("json");
        Assert.Equal("GraphRAG", jsonProp.GetProperty("name").GetString());
        Assert.Equal(5L, jsonProp.GetProperty("count").GetInt64());

        var timestamp = payload.GetProperty("timestamp").GetString();
        Assert.NotNull(timestamp);
        var parsedTimestamp = DateTime.Parse(timestamp!, CultureInfo.InvariantCulture, DateTimeStyles.AdjustToUniversal | DateTimeStyles.AssumeUniversal);
        Assert.Equal(DateTimeKind.Utc, parsedTimestamp.Kind);
    }

    [Fact]
    public async Task UpsertRelationship_ReturnsStoredProperties()
    {
        var store = _fixture.Services.GetRequiredKeyedService<IGraphStore>("postgres");
        await store.InitializeAsync();

        var sourceId = $"src-{Guid.NewGuid():N}";
        var targetId = $"dst-{Guid.NewGuid():N}";

        await store.UpsertNodeAsync(sourceId, "Person", new Dictionary<string, object?>());
        await store.UpsertNodeAsync(targetId, "Person", new Dictionary<string, object?>());

        var edgeProps = new Dictionary<string, object?>
        {
            ["weight"] = 0.42m,
            ["flag"] = true
        };

        await store.UpsertRelationshipAsync(sourceId, targetId, "KNOWS", edgeProps);

        var relationships = new List<GraphRelationship>();
        await foreach (var relationship in store.GetOutgoingRelationshipsAsync(sourceId))
        {
            relationships.Add(relationship);
        }

        var stored = Assert.Single(relationships, rel => rel.TargetId == targetId);
        Assert.Equal("KNOWS", stored.Type);
        Assert.Equal(sourceId, stored.SourceId);
        Assert.Equal(0.42d, Convert.ToDouble(stored.Properties["weight"], CultureInfo.InvariantCulture));
        Assert.True(Convert.ToBoolean(stored.Properties["flag"], CultureInfo.InvariantCulture));
    }

    [Fact]
    public async Task ExplainService_ReturnsPlanOutput()
    {
        var store = _fixture.Services.GetRequiredKeyedService<PostgresGraphStore>("postgres");
        await store.InitializeAsync();

        var nodeId = $"plan-{Guid.NewGuid():N}";
        await store.UpsertNodeAsync(nodeId, "Person", new Dictionary<string, object?> { ["name"] = "Planner" });

        var service = new PostgresExplainService(store, NullLogger<PostgresExplainService>.Instance);
        var plan = await service.GetFormattedPlanAsync("MATCH (n:Person) RETURN n LIMIT 1");

        Assert.Contains("EXPLAIN plan:", plan, StringComparison.Ordinal);
        Assert.Contains("Person", plan, StringComparison.OrdinalIgnoreCase);

        using var writer = new StringWriter();
        await service.WritePlanAsync("MATCH (n:Person) RETURN n LIMIT 1", writer, cancellationToken: default);
        Assert.False(string.IsNullOrWhiteSpace(writer.ToString()));
    }

    [Fact]
    public async Task IngestionBenchmark_UpsertsNodesAndRelationships()
    {
        var store = _fixture.Services.GetRequiredKeyedService<PostgresGraphStore>("postgres");
        await store.InitializeAsync();

        var prefix = Guid.NewGuid().ToString("N");
        var csv = $"source_id,target_id,weight{Environment.NewLine}{prefix}-100,{prefix}-200,0.5{Environment.NewLine}{prefix}-100,{prefix}-300,0.7{Environment.NewLine}";
        await using var stream = new MemoryStream(Encoding.UTF8.GetBytes(csv));

        var benchmark = new PostgresGraphIngestionBenchmark(store, NullLogger<PostgresGraphIngestionBenchmark>.Instance);
        var options = new PostgresIngestionBenchmarkOptions
        {
            EdgeLabel = "KNOWS",
            SourceLabel = "Person",
            TargetLabel = "Person",
            EdgePropertyColumns = { ["weight"] = "weight" }
        };

        var result = await benchmark.RunAsync(stream, options);

        Assert.Equal(3, result.NodesWritten);
        Assert.Equal(2, result.RelationshipsWritten);

        var relationships = new List<GraphRelationship>();
        await foreach (var relationship in store.GetOutgoingRelationshipsAsync($"{prefix}-100"))
        {
            relationships.Add(relationship);
        }

        Assert.Equal(2, relationships.Count);
        Assert.All(relationships, rel => Assert.StartsWith(prefix, rel.TargetId, StringComparison.Ordinal));
        Assert.All(relationships, rel => Assert.Equal("KNOWS", rel.Type));
    }

    private static async Task<JsonElement> GetNodePropertiesAsync(string connectionString, string nodeId)
    {
        await using var connection = new NpgsqlConnection(connectionString);
        await connection.OpenAsync();

        await ExecuteSqlAsync(connection, "LOAD 'age';");
        await ExecuteSqlAsync(connection, @"SET search_path = ag_catalog, ""$user"", public;");

        await using var command = connection.CreateCommand();
        command.CommandText =
@"SELECT ag_catalog.agtype_to_json(props)
FROM ag_catalog.cypher('graphrag'::name,
$$ MATCH (n { id: $node_id }) RETURN properties(n) AS props $$::cstring,
@params::ag_catalog.agtype) AS (props ag_catalog.agtype);";

        var parameter = new NpgsqlParameter("params", NpgsqlDbType.Unknown)
        {
            DataTypeName = "ag_catalog.agtype",
            Value = JsonSerializer.Serialize(new Dictionary<string, object?> { ["node_id"] = nodeId })
        };
        command.Parameters.Add(parameter);

        var json = (string?)await command.ExecuteScalarAsync() ?? "{}";
        using var document = JsonDocument.Parse(json);
        return document.RootElement.Clone();
    }

    private static async Task ExecuteSqlAsync(NpgsqlConnection connection, string sql)
    {
        await using var command = connection.CreateCommand();
        command.CommandText = sql;
        await command.ExecuteNonQueryAsync();
    }
}
