using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
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
        Assert.True(store.CapturedParameters!.ContainsKey("props"));
        var props = Assert.IsType<Dictionary<string, object?>>(store.CapturedParameters["props"]!);
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
        Assert.Equal("src-1", store.CapturedParameters!["source_id"]);
        Assert.Equal("dst-1", store.CapturedParameters["target_id"]);
        var props = Assert.IsType<Dictionary<string, object?>>(store.CapturedParameters["props"]!);
        Assert.Equal(0.42d, props["weight"]);
    }

    private sealed class TestPostgresGraphStore : PostgresGraphStore
    {
        public string? CapturedQuery { get; private set; }
        public IReadOnlyDictionary<string, object?>? CapturedParameters { get; private set; }

        public TestPostgresGraphStore()
            : base("Host=localhost;Username=test;Password=test;Database=test", "graph", NullLogger<PostgresGraphStore>.Instance)
        {
        }

        protected override Task ExecuteCypherAsync(string query, IReadOnlyDictionary<string, object?> parameters, CancellationToken cancellationToken)
        {
            CapturedQuery = query;
            CapturedParameters = parameters;
            return Task.CompletedTask;
        }
    }
}
