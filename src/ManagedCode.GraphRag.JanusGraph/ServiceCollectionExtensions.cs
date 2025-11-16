using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.JanusGraph;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddJanusGraphStore(this IServiceCollection services, string key, Action<JanusGraphStoreOptions> configure)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentException.ThrowIfNullOrWhiteSpace(key);
        ArgumentNullException.ThrowIfNull(configure);

        var options = new JanusGraphStoreOptions();
        configure(options);

        services.AddKeyedSingleton(key, options);
        services.AddKeyedSingleton<JanusGraphStore>(key, (sp, serviceKey) =>
        {
            var opts = sp.GetRequiredKeyedService<JanusGraphStoreOptions>(serviceKey);
            var logger = sp.GetRequiredService<ILogger<JanusGraphStore>>();
            return new JanusGraphStore(opts, logger);
        });

        services.AddKeyedSingleton<IGraphStore>(key, (sp, serviceKey) => sp.GetRequiredKeyedService<JanusGraphStore>(serviceKey));

        services.TryAddSingleton<JanusGraphStore>(sp => sp.GetRequiredKeyedService<JanusGraphStore>(key));
        services.TryAddSingleton<IGraphStore>(sp => sp.GetRequiredKeyedService<JanusGraphStore>(key));

        return services;
    }
}
