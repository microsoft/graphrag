using System.IO;
using System.Text;
using System.Threading.Tasks;
using GraphRag.Storage.Postgres;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Postgres;

public sealed class PostgresGraphIngestionBenchmarkTests
{
    [Fact]
    public async Task RunAsync_IngestsRelationshipsAndNodes()
    {
        var csv = "source_id,target_id,weight\n100,200,0.5\n100,300,0.7\n";
        await using var stream = new MemoryStream(Encoding.UTF8.GetBytes(csv));

        var store = new FakePostgresGraphStore(explainPlan: null);
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
        Assert.Equal(result.NodesWritten, store.NodeUpserts);
        Assert.Equal(result.RelationshipsWritten, store.RelationshipUpserts);
        Assert.Contains(store.ExecutedIndexCommands, command => command.Contains("prop_weight", System.StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public async Task RunAsync_SkipsIndexCreationWhenDisabled()
    {
        var csv = "source_id,target_id\n1,2\n";
        await using var stream = new MemoryStream(Encoding.UTF8.GetBytes(csv));

        var store = new FakePostgresGraphStore(options => options.AutoCreateIndexes = false, explainPlan: null);
        var benchmark = new PostgresGraphIngestionBenchmark(store, NullLogger<PostgresGraphIngestionBenchmark>.Instance);
        var options = new PostgresIngestionBenchmarkOptions
        {
            EdgeLabel = "REL",
            SourceLabel = "Doc",
            TargetLabel = "Doc",
            EnsurePropertyIndexes = false
        };

        var result = await benchmark.RunAsync(stream, options);

        Assert.Equal(2, result.NodesWritten);
        Assert.Equal(1, result.RelationshipsWritten);
        Assert.Empty(store.ExecutedIndexCommands);
    }
}
