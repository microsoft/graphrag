using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using GraphRag;
using GraphRag.Cache;
using GraphRag.Callbacks;
using GraphRag.Config;
using GraphRag.Indexing.Runtime;
using GraphRag.Storage;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Runtime;

public sealed class PipelineExecutorTests
{
    [Fact]
    public async Task ExecuteAsync_StopsOnException()
    {
        var services = new ServiceCollection().BuildServiceProvider();
        var context = new PipelineRunContext(
            new MemoryPipelineStorage(),
            new MemoryPipelineStorage(),
            new MemoryPipelineStorage(),
            new InMemoryPipelineCache(),
            NoopWorkflowCallbacks.Instance,
            new PipelineRunStats(),
            new PipelineState(),
            services);

        var pipeline = new WorkflowPipeline("test", new[]
        {
            new WorkflowStep("ok", (cfg, ctx, token) => ValueTask.FromResult(new WorkflowResult("done"))),
            new WorkflowStep("boom", (cfg, ctx, token) => throw new InvalidOperationException("fail")),
            new WorkflowStep("skipped", (cfg, ctx, token) => throw new Exception("should not run"))
        });

        var executor = new PipelineExecutor(new NullLogger<PipelineExecutor>());
        var results = new List<PipelineRunResult>();

        await foreach (var result in executor.ExecuteAsync(pipeline, new GraphRagConfig(), context))
        {
            results.Add(result);
        }

        Assert.Equal(2, results.Count);
        Assert.Null(results[0].Errors);
        Assert.NotNull(results[1].Errors);
        Assert.Equal("boom", results[1].Workflow);
    }

    [Fact]
    public async Task ExecuteAsync_HonoursStopSignal()
    {
        var services = new ServiceCollection().BuildServiceProvider();
        var context = new PipelineRunContext(
            new MemoryPipelineStorage(),
            new MemoryPipelineStorage(),
            new MemoryPipelineStorage(),
            new InMemoryPipelineCache(),
            NoopWorkflowCallbacks.Instance,
            new PipelineRunStats(),
            new PipelineState(),
            services);

        var pipeline = new WorkflowPipeline("stop", new[]
        {
            new WorkflowStep("first", (cfg, ctx, token) => ValueTask.FromResult(new WorkflowResult(null, true))),
            new WorkflowStep("second", (cfg, ctx, token) => ValueTask.FromResult(new WorkflowResult("should not happen")))
        });

        var executor = new PipelineExecutor(new NullLogger<PipelineExecutor>());
        var outputs = new List<PipelineRunResult>();
        await foreach (var result in executor.ExecuteAsync(pipeline, new GraphRagConfig(), context))
        {
            outputs.Add(result);
        }

        Assert.Single(outputs);
        Assert.Equal("first", outputs[0].Workflow);
    }
}
