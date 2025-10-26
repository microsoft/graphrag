using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace GraphRag.Storage;

public sealed class MemoryPipelineStorage : IPipelineStorage
{
    private readonly ConcurrentDictionary<string, StorageEntry> _entries;
    private readonly string _prefix;

    public MemoryPipelineStorage()
        : this(new ConcurrentDictionary<string, StorageEntry>(StringComparer.OrdinalIgnoreCase), string.Empty)
    {
    }

    private MemoryPipelineStorage(ConcurrentDictionary<string, StorageEntry> entries, string prefix)
    {
        _entries = entries;
        _prefix = prefix ?? string.Empty;
    }

    public async IAsyncEnumerable<PipelineStorageItem> FindAsync(Regex pattern, string? baseDir = null, IReadOnlyDictionary<string, object?>? fileFilter = null, int? maxCount = null, [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(pattern);

        var count = 0;
        foreach (var kvp in _entries)
        {
            cancellationToken.ThrowIfCancellationRequested();

            if (!IsUnderPrefix(kvp.Key))
            {
                continue;
            }

            var relativeKey = GetRelativeKey(kvp.Key);
            var match = pattern.Match(relativeKey);
            if (!match.Success)
            {
                continue;
            }

            var metadata = MergeMetadata(kvp.Value.Metadata, pattern, match);
            if (fileFilter is not null && fileFilter.Count > 0 && !MatchesFilter(metadata, fileFilter))
            {
                continue;
            }

            yield return new PipelineStorageItem(relativeKey, metadata, kvp.Value.CreatedAt);

            if (maxCount.HasValue && ++count >= maxCount.Value)
            {
                yield break;
            }
        }

        await Task.CompletedTask;
    }

    public Task<Stream?> GetAsync(string key, bool asBytes = false, Encoding? encoding = null, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var qualified = Qualify(key);
        if (!_entries.TryGetValue(qualified, out var entry))
        {
            return Task.FromResult<Stream?>(null);
        }

        var buffer = entry.Data;
        if (!asBytes && encoding is not null)
        {
            var text = encoding.GetString(buffer);
            return Task.FromResult<Stream?>(new MemoryStream(encoding.GetBytes(text), writable: false));
        }

        return Task.FromResult<Stream?>(new MemoryStream(buffer, writable: false));
    }

    public async Task SetAsync(string key, Stream content, Encoding? encoding = null, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        ArgumentNullException.ThrowIfNull(content);

        using var memory = new MemoryStream();
        await content.CopyToAsync(memory, cancellationToken).ConfigureAwait(false);
        var buffer = memory.ToArray();

        var qualified = Qualify(key);
        _entries[qualified] = new StorageEntry(buffer, DateTimeOffset.UtcNow, new Dictionary<string, object?>());
    }

    public Task<bool> HasAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(_entries.ContainsKey(Qualify(key)));
    }

    public Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        _entries.TryRemove(Qualify(key), out _);
        return Task.CompletedTask;
    }

    public Task ClearAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        foreach (var key in _entries.Keys)
        {
            if (IsUnderPrefix(key))
            {
                _entries.TryRemove(key, out _);
            }
        }

        return Task.CompletedTask;
    }

    public IPipelineStorage CreateChild(string? name)
    {
        name ??= string.Empty;
        var childPrefix = string.IsNullOrEmpty(_prefix) ? name : string.Concat(_prefix, "/", name);
        return new MemoryPipelineStorage(_entries, childPrefix);
    }

    public IReadOnlyList<string> Keys
    {
        get
        {
            return _entries.Keys
                .Where(IsUnderPrefix)
                .Select(GetRelativeKey)
                .ToArray();
        }
    }

    public Task<DateTimeOffset?> GetCreationDateAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(_entries.TryGetValue(Qualify(key), out var value) ? value.CreatedAt : (DateTimeOffset?)null);
    }

    private bool IsUnderPrefix(string key)
    {
        if (string.IsNullOrEmpty(_prefix))
        {
            return true;
        }

        return key.StartsWith(_prefix + "/", StringComparison.OrdinalIgnoreCase) || string.Equals(key, _prefix, StringComparison.OrdinalIgnoreCase);
    }

    private string GetRelativeKey(string key)
    {
        if (string.IsNullOrEmpty(_prefix))
        {
            return key;
        }

        return key.StartsWith(_prefix + "/", StringComparison.OrdinalIgnoreCase)
            ? key.Substring(_prefix.Length + 1)
            : key.Substring(_prefix.Length);
    }

    private string Qualify(string key)
    {
        if (string.IsNullOrEmpty(_prefix))
        {
            return key;
        }

        return string.Concat(_prefix, "/", key);
    }

    private static Dictionary<string, object?> MergeMetadata(IReadOnlyDictionary<string, object?> existing, Regex pattern, Match match)
    {
        var metadata = existing.Count > 0
            ? new Dictionary<string, object?>(existing, StringComparer.OrdinalIgnoreCase)
            : new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);

        foreach (var groupName in pattern.GetGroupNames())
        {
            if (string.Equals(groupName, "0", StringComparison.Ordinal))
            {
                continue;
            }

            var group = match.Groups[groupName];
            if (group.Success)
            {
                metadata[groupName] = group.Value;
            }
        }

        return metadata;
    }

    private static bool MatchesFilter(IReadOnlyDictionary<string, object?> metadata, IReadOnlyDictionary<string, object?> filter)
    {
        foreach (var kvp in filter)
        {
            if (!metadata.TryGetValue(kvp.Key, out var value) || value is null)
            {
                return false;
            }

            var candidate = value.ToString() ?? string.Empty;
            var pattern = kvp.Value?.ToString();

            if (string.IsNullOrEmpty(pattern))
            {
                continue;
            }

            if (!Regex.IsMatch(candidate, pattern, RegexOptions.IgnoreCase | RegexOptions.CultureInvariant))
            {
                return false;
            }
        }

        return true;
    }

    private sealed record StorageEntry(byte[] Data, DateTimeOffset CreatedAt, IReadOnlyDictionary<string, object?> Metadata);
}
