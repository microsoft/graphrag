using GraphRag.Cache;

namespace ManagedCode.GraphRag.Tests.Infrastructure;

internal sealed class StubPipelineCache : IPipelineCache
{
    public Task<object?> GetAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult<object?>(null);
    }

    public Task SetAsync(string key, object? value, IReadOnlyDictionary<string, object?>? debugData = null, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.CompletedTask;
    }

    public Task<bool> HasAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(false);
    }

    public Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.CompletedTask;
    }

    public Task ClearAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.CompletedTask;
    }

    public IPipelineCache CreateChild(string name)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(name);
        return this;
    }
}
