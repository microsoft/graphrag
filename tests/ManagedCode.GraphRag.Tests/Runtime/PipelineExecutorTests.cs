using GraphRag.Callbacks;
using GraphRag.Config;
using GraphRag.Indexing.Runtime;
using GraphRag.Logging;
using GraphRag.Storage;
using ManagedCode.GraphRag.Tests.Infrastructure;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;

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
            new StubPipelineCache(),
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
            new StubPipelineCache(),
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

    [Fact]
    public async Task ExecuteAsync_InvokesCallbacksAndUpdatesStats()
    {
        var services = new ServiceCollection().BuildServiceProvider();
        var callbacks = new RecordingCallbacks();
        var stats = new PipelineRunStats();
        var context = new PipelineRunContext(
            new MemoryPipelineStorage(),
            new MemoryPipelineStorage(),
            new MemoryPipelineStorage(),
            new StubPipelineCache(),
            callbacks,
            stats,
            new PipelineState(),
            services);

        var pipeline = new WorkflowPipeline("stats", new[]
        {
            new WorkflowStep("first", async (cfg, ctx, token) =>
            {
                await Task.Delay(5, token);
                return new WorkflowResult("ok");
            }),
            new WorkflowStep("second", (cfg, ctx, token) => ValueTask.FromResult(new WorkflowResult("done")))
        });

        var executor = new PipelineExecutor(new NullLogger<PipelineExecutor>());
        var results = new List<PipelineRunResult>();

        await foreach (var result in executor.ExecuteAsync(pipeline, new GraphRagConfig(), context))
        {
            results.Add(result);
        }

        Assert.Equal(new[] { "first", "second" }, callbacks.WorkflowStarts);
        Assert.Equal(callbacks.WorkflowStarts, callbacks.WorkflowEnds);
        Assert.Equal(2, callbacks.PipelineEndResults?.Count);
        Assert.True(callbacks.PipelineStartedWith?.SequenceEqual(pipeline.Names));

        Assert.Equal(2, results.Count);
        Assert.All(results, r => Assert.Null(r.Errors));

        Assert.True(stats.TotalRuntime >= 0);
        Assert.True(stats.Workflows.ContainsKey("first"));
        Assert.True(stats.Workflows["first"].ContainsKey("overall"));
        Assert.True(stats.Workflows.ContainsKey("second"));
        Assert.True(stats.Workflows["second"].ContainsKey("overall"));
    }

    [Fact]
    public async Task ExecuteAsync_RecordsExceptionInResultsAndStats()
    {
        var services = new ServiceCollection().BuildServiceProvider();
        var stats = new PipelineRunStats();
        var callbacks = new RecordingCallbacks();
        var context = new PipelineRunContext(
            new MemoryPipelineStorage(),
            new MemoryPipelineStorage(),
            new MemoryPipelineStorage(),
            new StubPipelineCache(),
            callbacks,
            stats,
            new PipelineState(),
            services);

        var failure = new InvalidOperationException("fail");
        var pipeline = new WorkflowPipeline("failing", new[]
        {
            new WorkflowStep("good", (cfg, ctx, token) => ValueTask.FromResult(new WorkflowResult("done"))),
            new WorkflowStep("bad", (cfg, ctx, token) => throw failure),
            new WorkflowStep("skipped", (cfg, ctx, token) => ValueTask.FromResult(new WorkflowResult("nope")))
        });

        var executor = new PipelineExecutor(new NullLogger<PipelineExecutor>());
        var results = new List<PipelineRunResult>();

        await foreach (var result in executor.ExecuteAsync(pipeline, new GraphRagConfig(), context))
        {
            results.Add(result);
        }

        Assert.Equal(2, results.Count);
        Assert.Null(results[0].Errors);
        var errorResult = results[1];
        Assert.NotNull(errorResult.Errors);
        var captured = Assert.Single(errorResult.Errors!);
        Assert.Same(failure, captured);

        Assert.Equal(new[] { "good", "bad" }, callbacks.WorkflowStarts);
        Assert.Equal(callbacks.WorkflowStarts, callbacks.WorkflowEnds);
        Assert.Equal(2, callbacks.PipelineEndResults?.Count);

        Assert.True(stats.Workflows.ContainsKey("good"));
        Assert.True(stats.Workflows.ContainsKey("bad"));
        Assert.False(stats.Workflows.ContainsKey("skipped"));
        Assert.True(stats.TotalRuntime >= 0);
    }

    private sealed class RecordingCallbacks : IWorkflowCallbacks
    {
        public IReadOnlyList<string>? PipelineStartedWith { get; private set; }
        public List<string> WorkflowStarts { get; } = new();
        public List<string> WorkflowEnds { get; } = new();
        public IReadOnlyList<PipelineRunResult>? PipelineEndResults { get; private set; }
        public List<ProgressSnapshot> ProgressUpdates { get; } = new();

        public void PipelineStart(IReadOnlyList<string> names)
        {
            PipelineStartedWith = names.ToArray();
        }

        public void PipelineEnd(IReadOnlyList<PipelineRunResult> results)
        {
            PipelineEndResults = results.ToArray();
        }

        public void WorkflowStart(string name, object? instance)
        {
            WorkflowStarts.Add(name);
        }

        public void WorkflowEnd(string name, object? instance)
        {
            WorkflowEnds.Add(name);
        }

        public void ReportProgress(ProgressSnapshot progress)
        {
            ProgressUpdates.Add(progress);
        }
    }
}
