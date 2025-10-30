using GraphRag;
using GraphRag.Chunking;
using GraphRag.Indexing.Runtime;
using ManagedCode.GraphRag.Tests.Infrastructure;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace ManagedCode.GraphRag.Tests.Runtime;

public sealed class ServiceCollectionExtensionsTests
{
    [Fact]
    public void AddGraphRag_RegistersCoreServices()
    {
        var services = new ServiceCollection();
        services.AddSingleton(typeof(ILogger<>), typeof(NullLogger<>));
        services.AddSingleton<IChatClient>(new TestChatClientFactory().CreateClient());
        services.AddGraphRag();
        using var provider = services.BuildServiceProvider();

        Assert.NotNull(provider.GetRequiredService<IChunkerResolver>());
        Assert.NotNull(provider.GetRequiredService<PipelineExecutor>());
    }
}
