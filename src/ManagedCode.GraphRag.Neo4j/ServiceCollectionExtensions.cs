using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Logging;
using Neo4j.Driver;

namespace GraphRag.Storage.Neo4j;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddNeo4jGraphStore(this IServiceCollection services, string key, Action<Neo4jGraphStoreOptions> configure)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentException.ThrowIfNullOrWhiteSpace(key);
        ArgumentNullException.ThrowIfNull(configure);

        var options = new Neo4jGraphStoreOptions();
        configure(options);

        services.AddKeyedSingleton(key, options);
        services.AddKeyedSingleton<Neo4jGraphStore>(key, (sp, serviceKey) =>
        {
            var opts = sp.GetRequiredKeyedService<Neo4jGraphStoreOptions>(serviceKey);
            var logger = sp.GetRequiredService<ILogger<Neo4jGraphStore>>();
            var driver = opts.DriverFactory?.Invoke(opts) ?? CreateDriver(opts);
            return new Neo4jGraphStore(driver, logger);
        });
        services.AddKeyedSingleton<IGraphStore>(key, (sp, serviceKey) => sp.GetRequiredKeyedService<Neo4jGraphStore>(serviceKey));

        services.TryAddSingleton<Neo4jGraphStore>(sp => sp.GetRequiredKeyedService<Neo4jGraphStore>(key));
        services.TryAddSingleton<IGraphStore>(sp => sp.GetRequiredKeyedService<Neo4jGraphStore>(key));

        return services;
    }

    private static IDriver CreateDriver(Neo4jGraphStoreOptions options)
    {
        var authToken = options.AuthTokenFactory?.Invoke(options) ?? AuthTokens.Basic(options.Username, options.Password);
        return GraphDatabase.Driver(options.Uri, authToken, config => options.ConfigureDriver?.Invoke(config));
    }
}

public sealed class Neo4jGraphStoreOptions
{
    public string Uri { get; set; } = "bolt://localhost:7687";

    public string Username { get; set; } = "neo4j";

    public string Password { get; set; } = "neo4j";

    public Func<Neo4jGraphStoreOptions, IAuthToken>? AuthTokenFactory { get; set; }

    public Action<ConfigBuilder>? ConfigureDriver { get; set; }

    public Func<Neo4jGraphStoreOptions, IDriver>? DriverFactory { get; set; }
}
