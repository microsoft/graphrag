using System.Collections.Concurrent;

namespace GraphRag.Cache;

public sealed class InMemoryPipelineCache : IPipelineCache
{
    private readonly ConcurrentDictionary<string, CacheEntry> _entries;

    public InMemoryPipelineCache()
        : this(new ConcurrentDictionary<string, CacheEntry>(StringComparer.OrdinalIgnoreCase))
    {
    }

    private InMemoryPipelineCache(ConcurrentDictionary<string, CacheEntry> entries)
    {
        _entries = entries;
    }

    public Task<object?> GetAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(_entries.TryGetValue(key, out var value) ? value.Value : null);
    }

    public Task SetAsync(string key, object? value, IReadOnlyDictionary<string, object?>? debugData = null, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        _entries[key] = new CacheEntry(value, debugData);
        return Task.CompletedTask;
    }

    public Task<bool> HasAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(_entries.ContainsKey(key));
    }

    public Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        _entries.TryRemove(key, out _);
        return Task.CompletedTask;
    }

    public Task ClearAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        _entries.Clear();
        return Task.CompletedTask;
    }

    public IPipelineCache CreateChild(string name)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(name);
        return new InMemoryPipelineCache(_entries);
    }

    private sealed record CacheEntry(object? Value, IReadOnlyDictionary<string, object?>? DebugData);
}
