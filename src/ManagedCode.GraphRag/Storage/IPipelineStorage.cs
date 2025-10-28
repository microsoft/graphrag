using System.Text;
using System.Text.RegularExpressions;

namespace GraphRag.Storage;

public interface IPipelineStorage
{
    IAsyncEnumerable<PipelineStorageItem> FindAsync(
        Regex pattern,
        string? baseDir = null,
        IReadOnlyDictionary<string, object?>? fileFilter = null,
        int? maxCount = null,
        CancellationToken cancellationToken = default);

    Task<Stream?> GetAsync(string key, bool asBytes = false, Encoding? encoding = null, CancellationToken cancellationToken = default);

    Task SetAsync(string key, Stream content, Encoding? encoding = null, CancellationToken cancellationToken = default);

    Task<bool> HasAsync(string key, CancellationToken cancellationToken = default);

    Task DeleteAsync(string key, CancellationToken cancellationToken = default);

    Task ClearAsync(CancellationToken cancellationToken = default);

    IPipelineStorage CreateChild(string? name);

    IReadOnlyList<string> Keys { get; }

    Task<DateTimeOffset?> GetCreationDateAsync(string key, CancellationToken cancellationToken = default);
}

public sealed record PipelineStorageItem(string Path, IReadOnlyDictionary<string, object?> Metadata, DateTimeOffset? CreatedAt);
