using GraphRag.Cache;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Cache;

public sealed class InMemoryPipelineCacheTests
{
    [Fact]
    public async Task CacheStoresAndRetrievesValues()
    {
        var cache = new InMemoryPipelineCache();
        await cache.SetAsync("key", "value");

        Assert.True(await cache.HasAsync("key"));
        Assert.Equal("value", await cache.GetAsync("key"));

        await cache.DeleteAsync("key");
        Assert.False(await cache.HasAsync("key"));
    }

    [Fact]
    public async Task CreateChild_SharesUnderlyingEntries()
    {
        var cache = new InMemoryPipelineCache();
        var child = cache.CreateChild("child");

        await cache.SetAsync("shared", 42);
        Assert.Equal(42, await child.GetAsync("shared"));

        await child.ClearAsync();
        Assert.False(await cache.HasAsync("shared"));
    }
}
