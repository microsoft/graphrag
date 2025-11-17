using System.Text;
using GraphRag.Graphs;
using GraphRag.Storage.Postgres;
using ManagedCode.GraphRag.Tests.Integration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;

namespace ManagedCode.GraphRag.Tests.Storage.Postgres;

[Collection(nameof(GraphRagApplicationCollection))]
public sealed class PostgresDiagnosticTests(GraphRagApplicationFixture fixture)
{
    [Fact]
    public async Task PostgresExplainService_ReturnsPlanOutput()
    {
        var store = fixture.Services.GetKeyedService<PostgresGraphStore>("postgres");
        if (store is null)
        {
            return;
        }

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
    public async Task PostgresIngestionBenchmark_UpsertsNodesAndRelationships()
    {
        var store = fixture.Services.GetKeyedService<PostgresGraphStore>("postgres");
        if (store is null)
        {
            return;
        }

        await store.InitializeAsync();

        var prefix = Guid.NewGuid().ToString("N");
        var csv = $"source_id,target_id,weight{Environment.NewLine}{prefix}-100,{prefix}-200,0.5{Environment.NewLine}{prefix}-100,{prefix}-300,0.7{Environment.NewLine}";
        await using var stream = new MemoryStream(Encoding.UTF8.GetBytes(csv));

        var benchmark = new PostgresGraphIngestionBenchmark(store, NullLogger<PostgresGraphIngestionBenchmark>.Instance);
        var options = new PostgresIngestionBenchmarkOptions
        {
            EdgeLabel = "KNOWS",
            SourceLabel = "Person",
            TargetLabel = "Person"
        };
        options.EdgePropertyColumns["weight"] = "weight";

        var result = await benchmark.RunAsync(stream, options);

        Assert.Equal(3, result.NodesWritten);
        Assert.Equal(2, result.RelationshipsWritten);

        var relationships = new List<GraphRelationship>();
        await foreach (var relationship in store.GetOutgoingRelationshipsAsync($"{prefix}-100"))
        {
            relationships.Add(relationship);
        }

        Assert.Equal(2, relationships.Count);
        Assert.All(relationships, rel => Assert.Equal("KNOWS", rel.Type));
    }
}
