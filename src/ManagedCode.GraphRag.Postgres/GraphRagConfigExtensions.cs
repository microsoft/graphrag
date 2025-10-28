using GraphRag.Config;

namespace GraphRag.Storage.Postgres;

public static class GraphRagConfigExtensions
{
    private const string PostgresGraphsKey = "postgres_graphs";

    public static Dictionary<string, PostgresGraphStoreConfig> GetPostgresGraphStores(this GraphRagConfig config)
    {
        ArgumentNullException.ThrowIfNull(config);

        if (!config.Extensions.TryGetValue(PostgresGraphsKey, out var value) || value is not Dictionary<string, PostgresGraphStoreConfig> typed)
        {
            typed = new Dictionary<string, PostgresGraphStoreConfig>(StringComparer.OrdinalIgnoreCase);
            config.Extensions[PostgresGraphsKey] = typed;
        }

        return typed;
    }

    public static void SetPostgresGraphStores(this GraphRagConfig config, Dictionary<string, PostgresGraphStoreConfig> stores)
    {
        ArgumentNullException.ThrowIfNull(config);
        config.Extensions[PostgresGraphsKey] = stores ?? new Dictionary<string, PostgresGraphStoreConfig>(StringComparer.OrdinalIgnoreCase);
    }
}
