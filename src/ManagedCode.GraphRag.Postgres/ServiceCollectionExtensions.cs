using System;
using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.Postgres;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddPostgresGraphStore(this IServiceCollection services, string key, Action<PostgresGraphStoreOptions> configure, bool makeDefault = false)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentException.ThrowIfNullOrWhiteSpace(key);
        ArgumentNullException.ThrowIfNull(configure);

        var options = new PostgresGraphStoreOptions();
        configure(options);

        services.AddKeyedSingleton<PostgresGraphStoreOptions>(key, (_, _) => options);
        services.AddKeyedSingleton<PostgresGraphStore>(key, (sp, serviceKey) =>
        {
            var opts = sp.GetRequiredKeyedService<PostgresGraphStoreOptions>(serviceKey);
            var logger = sp.GetRequiredService<ILogger<PostgresGraphStore>>();
            return new PostgresGraphStore(opts.ConnectionString, opts.GraphName, logger);
        });
        services.AddKeyedSingleton<IGraphStore>(key, (sp, serviceKey) => sp.GetRequiredKeyedService<PostgresGraphStore>(serviceKey));

        if (makeDefault)
        {
            services.AddSingleton(sp => sp.GetRequiredKeyedService<PostgresGraphStore>(key));
            services.AddSingleton<IGraphStore>(sp => sp.GetRequiredKeyedService<PostgresGraphStore>(key));
        }

        return services;
    }
}

public sealed class PostgresGraphStoreOptions
{
    public string ConnectionString { get; set; } = string.Empty;

    public string GraphName { get; set; } = "graphrag";
}
