using GraphRag.Graphs;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

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

        services.AddKeyedSingleton<JanusGraphStore, JanusGraphStore>(key);

        services.AddKeyedSingleton<IGraphStore, JanusGraphStore>(key);

        services.TryAddSingleton(options);
        services.TryAddSingleton<JanusGraphStore, JanusGraphStore>();
        services.TryAddSingleton<IGraphStore, JanusGraphStore>();

        return services;
    }
}
