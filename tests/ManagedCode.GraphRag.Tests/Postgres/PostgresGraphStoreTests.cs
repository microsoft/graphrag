using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using GraphRag.Constants;
using GraphRag.Storage.Postgres;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Postgres;

public sealed class PostgresGraphStoreTests
{
    [Fact]
    public async Task UpsertNodeAsync_UsesParameterPayload()
    {
        var store = new TestPostgresGraphStore();

        var properties = new Dictionary<string, object?>
        {
            ["name"] = "Alice'; DROP TABLE nodes; --",
            ["score"] = 42
        };

        await store.UpsertNodeAsync("user-1", "Person", properties);

        Assert.NotNull(store.CapturedQuery);
        Assert.DoesNotContain("DROP TABLE", store.CapturedQuery, System.StringComparison.OrdinalIgnoreCase);
        Assert.NotNull(store.CapturedParameters);
        Assert.True(store.CapturedParameters!.ContainsKey(CypherParameterNames.Properties));
        var props = Assert.IsType<Dictionary<string, object?>>(store.CapturedParameters[CypherParameterNames.Properties]!);
        Assert.Equal("Alice'; DROP TABLE nodes; --", props["name"]);
        Assert.Equal(42L, props["score"]); // numeric values coerced to Int64
    }

    [Fact]
    public async Task UpsertRelationshipAsync_UsesParameterPayload()
    {
        var store = new TestPostgresGraphStore();

        var properties = new Dictionary<string, object?>
        {
            ["weight"] = 0.42m
        };

        await store.UpsertRelationshipAsync("src-1", "dst-1", "KNOWS", properties);

        Assert.NotNull(store.CapturedQuery);
        Assert.Contains("MERGE (source)-[rel:KNOWS]->(target)", store.CapturedQuery);
        Assert.NotNull(store.CapturedParameters);
        Assert.Equal("src-1", store.CapturedParameters![CypherParameterNames.SourceId]);
        Assert.Equal("dst-1", store.CapturedParameters[CypherParameterNames.TargetId]);
        var props = Assert.IsType<Dictionary<string, object?>>(store.CapturedParameters[CypherParameterNames.Properties]!);
        Assert.Equal(0.42d, props["weight"]);
    }

    [Fact]
    public async Task UpsertNodeAsync_NormalizesNestedPropertyValues()
    {
        var store = new TestPostgresGraphStore();
        var properties = new Dictionary<string, object?>
        {
            ["intValue"] = 1,
            ["boolValue"] = true,
            ["array"] = new object?[] { "alpha", 2, false },
            ["objectValue"] = new Dictionary<string, object?> { ["inner"] = "value" },
            ["bytes"] = Encoding.UTF8.GetBytes("abc"),
            ["timestamp"] = new DateTime(2024, 1, 1, 8, 30, 0, DateTimeKind.Local),
            ["id"] = "ignored-by-converter"
        };

        using var json = JsonDocument.Parse("{\"name\":\"GraphRAG\",\"count\":5}");
        properties["json"] = json.RootElement.Clone();

        await store.UpsertNodeAsync("node-2", "Entity", properties);

        var payload = Assert.IsType<Dictionary<string, object?>>(store.CapturedParameters![CypherParameterNames.Properties]!);
        Assert.False(payload.ContainsKey(EntityPropertyNames.Id));
        Assert.Equal(1L, Convert.ToInt64(payload["intValue"], CultureInfo.InvariantCulture));
        Assert.Equal(true, payload["boolValue"]);

        var list = Assert.IsType<List<object?>>(payload["array"]);
        Assert.Equal("alpha", list[0]);
        Assert.Equal(2L, Convert.ToInt64(list[1], CultureInfo.InvariantCulture));
        Assert.Equal(false, list[2]);

        var nested = Assert.IsType<Dictionary<string, object?>>(payload["objectValue"]);
        Assert.Equal("value", nested["inner"]);

        Assert.Equal(Convert.ToBase64String(Encoding.UTF8.GetBytes("abc")), payload["bytes"]);

        var jsonDict = Assert.IsType<Dictionary<string, object?>>(payload["json"]);
        Assert.Equal("GraphRAG", jsonDict["name"]);
        Assert.Equal(5L, Convert.ToInt64(jsonDict["count"], CultureInfo.InvariantCulture));

        var timestamp = Assert.IsType<DateTime>(payload["timestamp"]!);
        Assert.Equal(DateTimeKind.Utc, timestamp.Kind);
    }

    [Fact]
    public async Task UpsertNodeAsync_CreatesDefaultIndexesOnce()
    {
        var store = new TestPostgresGraphStore();

        await store.UpsertNodeAsync("node-1", "Person", new Dictionary<string, object?>());
        await store.UpsertNodeAsync("node-2", "Person", new Dictionary<string, object?>());

        Assert.NotEmpty(store.ExecutedIndexCommands);
        Assert.All(new[] { "id", "props" }, suffix => Assert.Contains(store.ExecutedIndexCommands, cmd => cmd.Contains($"idx_graph_vertex_person_{suffix}", StringComparison.OrdinalIgnoreCase)));
        Assert.True(store.ExecutedIndexCommands.Count <= 2);
    }

    [Fact]
    public async Task UpsertRelationshipAsync_CreatesEdgeIndexes()
    {
        var store = new TestPostgresGraphStore();

        await store.UpsertRelationshipAsync("src", "dst", "KNOWS", new Dictionary<string, object?>());

        Assert.Contains(store.ExecutedIndexCommands, cmd => cmd.Contains("idx_graph_edge_knows_start_id", StringComparison.OrdinalIgnoreCase));
        Assert.Contains(store.ExecutedIndexCommands, cmd => cmd.Contains("idx_graph_edge_knows_end_id", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public async Task EnsurePropertyKeyIndexAsync_BuildsTargetedIndex()
    {
        var store = new TestPostgresGraphStore();

        await store.EnsurePropertyKeyIndexAsync("Person", "Email", isEdge: false);

        Assert.Contains(store.ExecutedIndexCommands, cmd => cmd.Contains("idx_graph_vertex_person_prop_email", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public async Task ExplainAsync_WrapsQueryWithExplain()
    {
        var store = new TestPostgresGraphStore();
        var plan = await store.ExplainAsync("MATCH (n:Person) RETURN n", new Dictionary<string, object?> { ["limit"] = 10 });

        Assert.NotEmpty(plan);
        var explainInvocation = Assert.Single(store.CapturedExplainInvocations);
        Assert.StartsWith("EXPLAIN", explainInvocation.Query, StringComparison.Ordinal);
        Assert.Contains("limit", explainInvocation.Parameters, StringComparison.Ordinal);
    }

    private sealed class TestPostgresGraphStore : PostgresGraphStore
    {
        public string? CapturedQuery { get; private set; }
        public IReadOnlyDictionary<string, object?>? CapturedParameters { get; private set; }
        public List<string> ExecutedIndexCommands { get; } = new();
        public List<(string Query, string Parameters)> CapturedExplainInvocations { get; } = new();

        public TestPostgresGraphStore()
            : base(new PostgresGraphStoreOptions
            {
                ConnectionString = "Host=localhost;Username=test;Password=test;Database=test",
                GraphName = "graph",
                AutoCreateIndexes = true
            }, NullLogger<PostgresGraphStore>.Instance)
        {
        }

        protected override Task ExecuteCypherAsync(string query, IReadOnlyDictionary<string, object?> parameters, CancellationToken cancellationToken)
        {
            CapturedQuery = query;
            CapturedParameters = parameters;
            return Task.CompletedTask;
        }

        protected override Task<string?> ResolveLabelRelationAsync(string label, bool isEdge, CancellationToken cancellationToken)
        {
            var relation = isEdge ? $"\"graph\".\"edge_{label.ToLowerInvariant()}\"" : $"\"graph\".\"vertex_{label.ToLowerInvariant()}\"";
            return Task.FromResult<string?>(relation);
        }

        protected override Task ExecuteIndexCommandsAsync(IEnumerable<string> commands, CancellationToken cancellationToken)
        {
            ExecutedIndexCommands.AddRange(commands);
            return Task.CompletedTask;
        }

        protected override Task<IReadOnlyList<string>> ExecuteExplainAsync(string explainQuery, string parameterJson, CancellationToken cancellationToken)
        {
            CapturedExplainInvocations.Add((explainQuery, parameterJson));
            return Task.FromResult<IReadOnlyList<string>>(new[] { "Seq Scan" });
        }
    }
}
