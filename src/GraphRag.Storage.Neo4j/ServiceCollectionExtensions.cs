using System;
using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.Neo4j;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddNeo4jGraphStore(this IServiceCollection services, string key, Action<Neo4jGraphStoreOptions> configure, bool makeDefault = false)
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
            return new Neo4jGraphStore(opts.Uri, opts.Username, opts.Password, logger);
        });
        services.AddKeyedSingleton<IGraphStore>(key, (sp, serviceKey) => sp.GetRequiredKeyedService<Neo4jGraphStore>(serviceKey));

        if (makeDefault)
        {
            services.AddSingleton(sp => sp.GetRequiredKeyedService<Neo4jGraphStore>(key));
            services.AddSingleton<IGraphStore>(sp => sp.GetRequiredKeyedService<Neo4jGraphStore>(key));
        }

        return services;
    }
}

public sealed class Neo4jGraphStoreOptions
{
    public string Uri { get; set; } = "bolt://localhost:7687";

    public string Username { get; set; } = "neo4j";

    public string Password { get; set; } = "neo4j";
}
