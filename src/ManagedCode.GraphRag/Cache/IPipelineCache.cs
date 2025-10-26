using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace GraphRag.Cache;

public interface IPipelineCache
{
    Task<object?> GetAsync(string key, CancellationToken cancellationToken = default);

    Task SetAsync(string key, object? value, IReadOnlyDictionary<string, object?>? debugData = null, CancellationToken cancellationToken = default);

    Task<bool> HasAsync(string key, CancellationToken cancellationToken = default);

    Task DeleteAsync(string key, CancellationToken cancellationToken = default);

    Task ClearAsync(CancellationToken cancellationToken = default);

    IPipelineCache CreateChild(string name);
}
