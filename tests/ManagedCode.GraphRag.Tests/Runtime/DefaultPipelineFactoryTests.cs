using System.Threading.Tasks;
using GraphRag.Indexing.Runtime;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Runtime;

public sealed class DefaultPipelineFactoryTests
{
    [Fact]
    public void BuildIndexingPipeline_ResolvesKeyedDelegates()
    {
        WorkflowDelegate first = (config, context, token) => ValueTask.FromResult(new WorkflowResult("first"));
        WorkflowDelegate second = (config, context, token) => ValueTask.FromResult(new WorkflowResult("second"));

        var services = new ServiceCollection();
        services.AddKeyedSingleton<WorkflowDelegate>("one", (_, _) => first);
        services.AddKeyedSingleton<WorkflowDelegate>("two", (_, _) => second);

        using var provider = services.BuildServiceProvider();
        var factory = new DefaultPipelineFactory(provider);

        var descriptor = new IndexingPipelineDescriptor("pipeline", new[] { "one", "two" });
        var pipeline = factory.BuildIndexingPipeline(descriptor);

        Assert.Equal("pipeline", pipeline.Name);
        Assert.Equal(new[] { "one", "two" }, pipeline.Names);

        Assert.Equal(first, pipeline.Steps[0].Delegate);
        Assert.Equal(second, pipeline.Steps[1].Delegate);
    }

    [Fact]
    public void BuildQueryPipeline_UsesQueryDescriptor()
    {
        WorkflowDelegate handler = (config, context, token) => ValueTask.FromResult(new WorkflowResult("query"));
        var services = new ServiceCollection();
        services.AddKeyedSingleton<WorkflowDelegate>("query-step", (_, _) => handler);

        using var provider = services.BuildServiceProvider();
        var factory = new DefaultPipelineFactory(provider);

        var descriptor = new QueryPipelineDescriptor("query", new[] { "query-step" });
        var pipeline = factory.BuildQueryPipeline(descriptor);

        Assert.Equal("query", pipeline.Name);
        Assert.Single(pipeline.Steps);
        Assert.Equal(handler, pipeline.Steps[0].Delegate);
    }
}
