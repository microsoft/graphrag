using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using GraphRag.Storage.Postgres;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Postgres;

public sealed class PostgresExplainServiceTests
{
    [Fact]
    public async Task GetFormattedPlanAsync_ReturnsIndentedPlan()
    {
        var plan = new List<string> { "Seq Scan on \"Person\" n" };
        var store = new FakePostgresGraphStore(explainPlan: plan);
        var service = new PostgresExplainService(store, NullLogger<PostgresExplainService>.Instance);

        var formatted = await service.GetFormattedPlanAsync("MATCH (n:Person) RETURN n");

        Assert.Contains("EXPLAIN plan:", formatted);
        Assert.Contains("Seq Scan", formatted);
    }

    [Fact]
    public async Task WritePlanAsync_WritesToProvidedWriter()
    {
        var plan = new List<string> { "Index Scan" };
        var store = new FakePostgresGraphStore(explainPlan: plan);
        var service = new PostgresExplainService(store, NullLogger<PostgresExplainService>.Instance);

        using var writer = new StringWriter();
        await service.WritePlanAsync("MATCH (n) RETURN n", writer, cancellationToken: CancellationToken.None);

        var output = writer.ToString();
        Assert.Contains("Index Scan", output);
    }

}
