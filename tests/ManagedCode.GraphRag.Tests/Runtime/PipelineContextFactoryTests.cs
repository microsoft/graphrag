using GraphRag.Callbacks;
using GraphRag.Indexing.Runtime;
using GraphRag.Storage;
using ManagedCode.GraphRag.Tests.Infrastructure;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Runtime;

public sealed class PipelineContextFactoryTests
{
    [Fact]
    public void Create_UsesProvidedComponents()
    {
        var input = new MemoryPipelineStorage();
        var output = new MemoryPipelineStorage();
        var previous = new MemoryPipelineStorage();
        var cache = new StubPipelineCache();
        var callbacks = WorkflowCallbacksManagerFactory();
        var stats = new PipelineRunStats();
        var state = new PipelineState();
        var services = new ServiceCollection().BuildServiceProvider();
        var context = PipelineContextFactory.Create(input, output, previous, cache, callbacks, stats, state, services, new Dictionary<string, object?> { ["flag"] = true });

        Assert.Same(input, context.InputStorage);
        Assert.Same(cache, context.Cache);
        Assert.Equal(true, context.Items?["flag"]);
    }

    [Fact]
    public void Create_ProvidesDefaultsWhenNull()
    {
        var context = PipelineContextFactory.Create();

        Assert.IsType<MemoryPipelineStorage>(context.InputStorage);
        Assert.Null(context.Cache);
        Assert.NotNull(context.Services);
    }

    private static IWorkflowCallbacks WorkflowCallbacksManagerFactory() => new WorkflowCallbacksManager();
}
