using GraphRag.Config;

namespace ManagedCode.GraphRag.Tests.Config;

public sealed class ConfigTests
{
    [Fact]
    public void StorageConfig_AllowsCustomValues()
    {
        var config = new StorageConfig
        {
            Type = StorageType.Memory,
            BaseDir = "data",
            ConnectionString = "conn",
            ContainerName = "container",
            StorageAccountBlobUrl = "https://example.com",
            CosmosDbAccountUrl = "https://cosmos.com"
        };

        Assert.Equal(StorageType.Memory, config.Type);
        Assert.Equal("data", config.BaseDir);
        Assert.Equal("conn", config.ConnectionString);
        Assert.Equal("container", config.ContainerName);
        Assert.Equal("https://example.com", config.StorageAccountBlobUrl);
        Assert.Equal("https://cosmos.com", config.CosmosDbAccountUrl);
    }

    [Fact]
    public void ReportingConfig_AllowsCustomValues()
    {
        var config = new ReportingConfig
        {
            Type = ReportingType.Blob,
            BaseDir = "reports",
            ConnectionString = "conn",
            ContainerName = "container",
            StorageAccountBlobUrl = "https://blob"
        };

        Assert.Equal(ReportingType.Blob, config.Type);
        Assert.Equal("reports", config.BaseDir);
        Assert.Equal("conn", config.ConnectionString);
    }

    [Fact]
    public void SnapshotsConfig_StoresFlags()
    {
        var config = new SnapshotsConfig
        {
            Embeddings = true,
            GraphMl = true,
            RawGraph = false
        };

        Assert.True(config.Embeddings);
        Assert.True(config.GraphMl);
        Assert.False(config.RawGraph);
    }

    [Fact]
    public void VectorStoreSchemaConfig_AllowsCustomization()
    {
        var config = new VectorStoreSchemaConfig
        {
            IdField = "id_field",
            VectorField = "vec",
            TextField = "text_field",
            AttributesField = "attrs",
            VectorSize = 42,
            IndexName = "index"
        };

        Assert.Equal("id_field", config.IdField);
        Assert.Equal("vec", config.VectorField);
        Assert.Equal(42, config.VectorSize);
        Assert.Equal("index", config.IndexName);
    }

    [Fact]
    public void GraphRagConfig_InitializesEmptyModelSet()
    {
        var config = new GraphRagConfig();

        Assert.Empty(config.Models);
    }
}
