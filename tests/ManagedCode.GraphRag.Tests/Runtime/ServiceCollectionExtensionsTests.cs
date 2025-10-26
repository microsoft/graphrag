using System.Threading.Tasks;
using GraphRag;
using GraphRag.Chunking;
using GraphRag.Indexing.Runtime;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Runtime;

public sealed class ServiceCollectionExtensionsTests
{
    [Fact]
    public void AddGraphRag_RegistersCoreServices()
    {
        var services = new ServiceCollection();
        services.AddSingleton(typeof(ILogger<>), typeof(NullLogger<>));
        services.AddGraphRag();
        using var provider = services.BuildServiceProvider();

        Assert.NotNull(provider.GetRequiredService<IChunkerResolver>());
        Assert.NotNull(provider.GetRequiredService<PipelineExecutor>());
    }

    [Fact]
    public void AddGraphRag_ConfigureAddsCustomStep()
    {
        WorkflowDelegate handler = (config, context, token) => ValueTask.FromResult(new WorkflowResult("custom"));
        var services = new ServiceCollection().AddGraphRag(builder => builder.AddStep("custom_step", handler));
        using var provider = services.BuildServiceProvider();

        var resolved = provider.GetRequiredKeyedService<WorkflowDelegate>("custom_step");
        Assert.Equal(handler, resolved);
    }
}
