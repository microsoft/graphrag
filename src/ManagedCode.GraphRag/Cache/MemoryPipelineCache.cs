using System.Collections.Concurrent;
using Microsoft.Extensions.Caching.Memory;

namespace GraphRag.Cache;

/// <summary>
/// <see cref="IPipelineCache"/> implementation backed by <see cref="IMemoryCache"/>.
/// </summary>
public sealed class MemoryPipelineCache : IPipelineCache
{
    private readonly IMemoryCache _memoryCache;
    private readonly string _scope;
    private readonly ConcurrentDictionary<string, byte> _keys;

    public MemoryPipelineCache(IMemoryCache memoryCache)
        : this(memoryCache, Guid.NewGuid().ToString("N"), new ConcurrentDictionary<string, byte>())
    {
    }

    private MemoryPipelineCache(IMemoryCache memoryCache, string scope, ConcurrentDictionary<string, byte> keys)
    {
        _memoryCache = memoryCache ?? throw new ArgumentNullException(nameof(memoryCache));
        _scope = scope;
        _keys = keys;
    }

    public Task<object?> GetAsync(string key, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(key);
        cancellationToken.ThrowIfCancellationRequested();

        if (_memoryCache.TryGetValue(GetCacheKey(key), out var value) && value is CacheEntry entry)
        {
            return Task.FromResult(entry.Value);
        }

        return Task.FromResult<object?>(null);
    }

    public Task SetAsync(string key, object? value, IReadOnlyDictionary<string, object?>? debugData = null, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(key);
        cancellationToken.ThrowIfCancellationRequested();

        var cacheKey = GetCacheKey(key);
        _memoryCache.Set(cacheKey, new CacheEntry(value, debugData));
        _keys[cacheKey] = 0;
        return Task.CompletedTask;
    }

    public Task<bool> HasAsync(string key, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(key);
        cancellationToken.ThrowIfCancellationRequested();

        return Task.FromResult(_memoryCache.TryGetValue(GetCacheKey(key), out _));
    }

    public Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(key);
        cancellationToken.ThrowIfCancellationRequested();

        var cacheKey = GetCacheKey(key);
        _memoryCache.Remove(cacheKey);
        _keys.TryRemove(cacheKey, out _);
        return Task.CompletedTask;
    }

    public Task ClearAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var scopePrefix = string.Concat(_scope, ":");

        foreach (var cacheKey in _keys.Keys)
        {
            if (!cacheKey.StartsWith(scopePrefix, StringComparison.Ordinal))
            {
                continue;
            }

            _memoryCache.Remove(cacheKey);
            _keys.TryRemove(cacheKey, out _);
        }

        return Task.CompletedTask;
    }

    public IPipelineCache CreateChild(string name)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(name);
        var childScope = string.Concat(_scope, ":", name);
        return new MemoryPipelineCache(_memoryCache, childScope, _keys);
    }

    private string GetCacheKey(string key)
    {
        return string.Concat(_scope, ":", key);
    }

    private sealed record CacheEntry(object? Value, IReadOnlyDictionary<string, object?>? DebugData);
}
