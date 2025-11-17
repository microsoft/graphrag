using GraphRag.Config;
using GraphRag.Storage.Postgres;

namespace ManagedCode.GraphRag.Tests.Config;

public sealed class PostgresGraphRagConfigExtensionsTests
{
    [Fact]
    public void GetPostgresGraphStores_ReturnsMutableDictionary()
    {
        var config = new GraphRagConfig();
        var stores = config.GetPostgresGraphStores();
        Assert.Empty(stores);

        stores["primary"] = new PostgresGraphStoreConfig { ConnectionString = "Host=localhost", GraphName = "g" };

        var replay = config.GetPostgresGraphStores();
        Assert.Equal("g", replay["primary"].GraphName);
    }

    [Fact]
    public void SetPostgresGraphStores_ReplacesExisting()
    {
        var config = new GraphRagConfig();
        var initial = new Dictionary<string, PostgresGraphStoreConfig>
        {
            ["default"] = new() { ConnectionString = "conn", GraphName = "g" }
        };

        config.SetPostgresGraphStores(initial);
        var stores = config.GetPostgresGraphStores();
        Assert.Equal("g", stores["default"].GraphName);

        config.SetPostgresGraphStores(null!);
        Assert.Empty(config.GetPostgresGraphStores());
    }
}
