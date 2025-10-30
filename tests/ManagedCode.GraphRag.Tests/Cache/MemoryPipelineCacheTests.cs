using System.Collections.Concurrent;
using System.Reflection;
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

    [Fact]
    public async Task DeleteAsync_RemovesTrackedKeyEvenWithDebugData()
    {
        var memoryCache = new MemoryCache(new MemoryCacheOptions());
        var cache = new MemoryPipelineCache(memoryCache);

        await cache.SetAsync("debug", 123, new Dictionary<string, object?> { ["token"] = "value" });
        var keys = GetTrackedKeys(cache);
        Assert.Contains(keys.Keys, key => key.EndsWith(":debug", StringComparison.Ordinal));

        await cache.DeleteAsync("debug");

        Assert.DoesNotContain(GetTrackedKeys(cache).Keys, key => key.EndsWith(":debug", StringComparison.Ordinal));
        Assert.False(await cache.HasAsync("debug"));
    }

    [Fact]
    public async Task CreateChild_AfterParentWrites_StillClearsChildEntries()
    {
        var memoryCache = new MemoryCache(new MemoryCacheOptions());
        var parent = new MemoryPipelineCache(memoryCache);

        await parent.SetAsync("root", "root");
        var child = parent.CreateChild("later-child");
        await child.SetAsync("inner", "child");

        await parent.ClearAsync();

        Assert.False(await parent.HasAsync("root"));
        Assert.False(await child.HasAsync("inner"));
    }

    private static ConcurrentDictionary<string, byte> GetTrackedKeys(MemoryPipelineCache cache)
    {
        var field = typeof(MemoryPipelineCache)
            .GetField("_keys", BindingFlags.NonPublic | BindingFlags.Instance)
            ?? throw new InvalidOperationException("Could not access keys field.");

        return (ConcurrentDictionary<string, byte>)field.GetValue(cache)!;
    }
}
