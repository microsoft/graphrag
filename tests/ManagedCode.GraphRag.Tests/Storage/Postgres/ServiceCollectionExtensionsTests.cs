using System.Collections.Generic;
using System.Threading.Tasks;
using GraphRag.Config;
using GraphRag.Graphs;
using GraphRag.Storage.Postgres;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Storage.Postgres;

public sealed class ServiceCollectionExtensionsTests
{
    [Fact]
    public async Task AddPostgresGraphStore_RegistersKeyedServices()
    {
        var services = new ServiceCollection();
        services.AddSingleton<ILogger<PostgresGraphStore>>(_ => NullLogger<PostgresGraphStore>.Instance);

        services.AddPostgresGraphStore("primary", options =>
        {
            options.ConnectionString = "Host=localhost";
            options.GraphName = "graph";
        });

        await using var provider = services.BuildServiceProvider();
        var store = provider.GetRequiredKeyedService<PostgresGraphStore>("primary");
        Assert.NotNull(store);
    }

    [Fact]
    public async Task AddPostgresGraphStore_CanRegisterDefault()
    {
        var services = new ServiceCollection();
        services.AddSingleton<ILogger<PostgresGraphStore>>(_ => NullLogger<PostgresGraphStore>.Instance);

        services.AddPostgresGraphStore("default", options =>
        {
            options.ConnectionString = "Host=localhost";
            options.GraphName = "graph";
        }, makeDefault: true);

        await using var provider = services.BuildServiceProvider();
        var store = provider.GetRequiredService<PostgresGraphStore>();
        var graphStore = provider.GetRequiredService<IGraphStore>();

        Assert.Same(store, graphStore);
    }

    [Fact]
    public async Task AddPostgresGraphStores_RegistersFromConfig()
    {
        var services = new ServiceCollection();
        services.AddSingleton<ILogger<PostgresGraphStore>>(_ => NullLogger<PostgresGraphStore>.Instance);

        var config = new GraphRagConfig();
        var graphs = config.GetPostgresGraphStores();
        graphs["primary"] = new PostgresGraphStoreConfig
        {
            ConnectionString = "Host=localhost",
            GraphName = "graph",
            AutoCreateIndexes = false,
            MakeDefault = true,
            VertexPropertyIndexes = new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase)
            {
                ["Person"] = new[] { "Email", "Name" }
            },
            EdgePropertyIndexes = new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase)
            {
                ["KNOWS"] = new[] { "Since" }
            }
        };

        services.AddPostgresGraphStores(config);

        await using var provider = services.BuildServiceProvider();

        var options = provider.GetRequiredKeyedService<PostgresGraphStoreOptions>("primary");
        Assert.False(options.AutoCreateIndexes);
        Assert.Contains("Person", options.VertexPropertyIndexes.Keys);
        Assert.Contains("KNOWS", options.EdgePropertyIndexes.Keys);

        var defaultStore = provider.GetRequiredService<IGraphStore>();
        Assert.NotNull(defaultStore);
    }
}
