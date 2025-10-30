using GraphRag.Cache;
using Microsoft.Extensions.Caching.Memory;

namespace ManagedCode.GraphRag.Tests.Cache;

public sealed class MemoryPipelineCacheTests
{
    [Fact]
    public async Task SetAndGet_ReturnsStoredValue()
    {
        var memoryCache = new MemoryCache(new MemoryCacheOptions());
        var cache = new MemoryPipelineCache(memoryCache);

        await cache.SetAsync("foo", 42);
        var value = await cache.GetAsync("foo");

        Assert.Equal(42, value);
        Assert.True(await cache.HasAsync("foo"));
    }

    [Fact]
    public async Task ClearAsync_RemovesEntries()
    {
        var memoryCache = new MemoryCache(new MemoryCacheOptions());
        var cache = new MemoryPipelineCache(memoryCache);

        await cache.SetAsync("foo", "bar");
        await cache.ClearAsync();

        Assert.False(await cache.HasAsync("foo"));
    }

    [Fact]
    public async Task ChildCache_IsolatedFromParent()
    {
        var memoryCache = new MemoryCache(new MemoryCacheOptions());
        var parent = new MemoryPipelineCache(memoryCache);
        var child = parent.CreateChild("child");

        await child.SetAsync("value", "child");

        Assert.False(await parent.HasAsync("value"));
        Assert.Equal("child", await child.GetAsync("value"));
    }

    [Fact]
    public async Task ClearAsync_RemovesChildEntries()
    {
        var memoryCache = new MemoryCache(new MemoryCacheOptions());
        var parent = new MemoryPipelineCache(memoryCache);
        var child = parent.CreateChild("child");

        await parent.SetAsync("parentValue", "parent");
        await child.SetAsync("childValue", "child");

        await parent.ClearAsync();

        Assert.False(await parent.HasAsync("parentValue"));
        Assert.False(await child.HasAsync("childValue"));
    }
}
