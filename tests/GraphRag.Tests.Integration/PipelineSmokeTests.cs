using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Aspire.Hosting;
using Aspire.Hosting.Testing;
using GraphRag.Core.Pipelines;
using GraphRag.Pipelines;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace GraphRag.Tests.Integration;

public sealed class PipelineSmokeTests
{
    [Fact]
    public async Task Pipeline_populates_each_registered_graph_store()
    {
        if (!string.Equals(Environment.GetEnvironmentVariable("GRAPH_RAG_ENABLE_ASPIRE"), "1", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        var builder = await DistributedApplicationTestingBuilder.CreateAsync<PipelineSmokeTests>(CancellationToken.None);
        GraphRagAspireAppHost.Configure((IDistributedApplicationBuilder)builder);

        await using var app = await builder.BuildAsync();
        await app.StartAsync();
        await using var scope = app.Services.CreateAsyncScope();

        var factory = scope.ServiceProvider.GetRequiredService<IPipelineFactory>();
        var steps = new List<string> { "neo4j-seed", "postgres-seed" };
        if (!string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable("COSMOS_EMULATOR_CONNECTION_STRING")))
        {
            steps.Add("cosmos-seed");
        }

        var pipeline = factory.BuildIndexingPipeline(new IndexingPipelineDescriptor("graph-seeding", steps));
        var context = new PipelineContext(new Dictionary<string, object?>(), scope.ServiceProvider, default);
        await pipeline.ExecuteAsync(context);

        Assert.Equal(1, context.Items["neo4j:relationship-count"]);
        Assert.Equal(1, context.Items["postgres:relationship-count"]);
        if (steps.Contains("cosmos-seed"))
        {
            Assert.Equal(1, context.Items["cosmos:relationship-count"]);
        }
    }
}
