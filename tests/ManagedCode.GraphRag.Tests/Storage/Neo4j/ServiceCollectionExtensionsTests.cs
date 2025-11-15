using GraphRag.Graphs;
using GraphRag.Storage.Neo4j;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace ManagedCode.GraphRag.Tests.Storage.Neo4j;

public sealed class ServiceCollectionExtensionsTests
{
    [Fact]
    public async Task AddNeo4jGraphStore_RegistersKeyedServices()
    {
        var services = new ServiceCollection();
        services.AddSingleton<ILogger<Neo4jGraphStore>>(_ => NullLogger<Neo4jGraphStore>.Instance);

        services.AddNeo4jGraphStore("primary", options =>
        {
            options.Uri = "bolt://localhost:7687";
            options.Username = "neo4j";
            options.Password = "pass";
        });

        await using var provider = services.BuildServiceProvider();
        var store = provider.GetRequiredKeyedService<Neo4jGraphStore>("primary");
        Assert.NotNull(store);
    }

    [Fact]
    public async Task AddNeo4jGraphStore_FirstStoreIsDefault()
    {
        var services = new ServiceCollection();
        services.AddSingleton<ILogger<Neo4jGraphStore>>(_ => NullLogger<Neo4jGraphStore>.Instance);

        services.AddNeo4jGraphStore("primary", options =>
        {
            options.Uri = "bolt://localhost:7687";
            options.Username = "neo4j";
            options.Password = "pass";
        });

        await using var provider = services.BuildServiceProvider();
        var keyed = provider.GetRequiredKeyedService<Neo4jGraphStore>("primary");
        var store = provider.GetRequiredService<Neo4jGraphStore>();
        var graphStore = provider.GetRequiredService<IGraphStore>();

        Assert.Same(keyed, store);
        Assert.Same(store, graphStore);
    }

    [Fact]
    public async Task AddNeo4jGraphStore_SubsequentStoresDoNotOverrideDefault()
    {
        var services = new ServiceCollection();
        services.AddSingleton<ILogger<Neo4jGraphStore>>(_ => NullLogger<Neo4jGraphStore>.Instance);

        services.AddNeo4jGraphStore("primary", options =>
        {
            options.Uri = "bolt://localhost:7687";
            options.Username = "neo4j";
            options.Password = "pass";
        });

        services.AddNeo4jGraphStore("secondary", options =>
        {
            options.Uri = "bolt://localhost:7688";
            options.Username = "neo";
            options.Password = "secret";
        });

        await using var provider = services.BuildServiceProvider();

        var defaultStore = provider.GetRequiredService<Neo4jGraphStore>();
        var graphStore = provider.GetRequiredService<IGraphStore>();
        var primaryStore = provider.GetRequiredKeyedService<Neo4jGraphStore>("primary");
        var secondaryStore = provider.GetRequiredKeyedService<Neo4jGraphStore>("secondary");
        var secondaryGraphStore = provider.GetRequiredKeyedService<IGraphStore>("secondary");

        Assert.Same(primaryStore, defaultStore);
        Assert.Same(defaultStore, graphStore);
        Assert.NotSame(primaryStore, secondaryStore);
        Assert.Same(secondaryStore, secondaryGraphStore);
    }
}
