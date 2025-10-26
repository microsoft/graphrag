using System;
using System.Text.Json;
using GraphRag.Graphs;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.Cosmos;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddCosmosGraphStore(this IServiceCollection services, string key, Action<CosmosGraphStoreOptions> configure, bool makeDefault = false)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentException.ThrowIfNullOrWhiteSpace(key);
        ArgumentNullException.ThrowIfNull(configure);

        var options = new CosmosGraphStoreOptions();
        configure(options);

        services.AddKeyedSingleton<CosmosGraphStoreOptions>(key, (_, _) => options);
        services.AddKeyedSingleton<CosmosClient>(key, (_, _) =>
        {
            var serializerOptions = new JsonSerializerOptions(JsonSerializerDefaults.Web)
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            };
            var cosmosOptions = new CosmosClientOptions
            {
                Serializer = new SystemTextJsonCosmosSerializer(serializerOptions)
            };

            return new CosmosClient(options.ConnectionString, cosmosOptions);
        });
        services.AddKeyedSingleton<CosmosGraphStore>(key, (sp, serviceKey) =>
        {
            var client = sp.GetRequiredKeyedService<CosmosClient>(serviceKey);
            var opts = sp.GetRequiredKeyedService<CosmosGraphStoreOptions>(serviceKey);
            var logger = sp.GetRequiredService<ILogger<CosmosGraphStore>>();
            return new CosmosGraphStore(client, opts.DatabaseId, opts.NodesContainerId, opts.EdgesContainerId, logger);
        });
        services.AddKeyedSingleton<IGraphStore>(key, (sp, serviceKey) => sp.GetRequiredKeyedService<CosmosGraphStore>(serviceKey));

        if (makeDefault)
        {
            services.AddSingleton(sp => sp.GetRequiredKeyedService<CosmosGraphStore>(key));
            services.AddSingleton<IGraphStore>(sp => sp.GetRequiredKeyedService<CosmosGraphStore>(key));
        }

        return services;
    }
}

public sealed class CosmosGraphStoreOptions
{
    public string ConnectionString { get; set; } = string.Empty;

    public string DatabaseId { get; set; } = "graphrag";

    public string NodesContainerId { get; set; } = "nodes";

    public string EdgesContainerId { get; set; } = "edges";
}
