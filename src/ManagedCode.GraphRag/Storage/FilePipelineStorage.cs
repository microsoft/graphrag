using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace GraphRag.Storage;

public sealed class FilePipelineStorage : IPipelineStorage
{
    private readonly string _root;

    public FilePipelineStorage(string root)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(root);
        _root = Path.GetFullPath(root);
        Directory.CreateDirectory(_root);
    }

    private FilePipelineStorage(string root, string subPath)
    {
        _root = Path.GetFullPath(Path.Combine(root, subPath));
        Directory.CreateDirectory(_root);
    }

    public async IAsyncEnumerable<PipelineStorageItem> FindAsync(
        Regex pattern,
        string? baseDir = null,
        IReadOnlyDictionary<string, object?>? fileFilter = null,
        int? maxCount = null,
        [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var searchRoot = string.IsNullOrEmpty(baseDir) ? _root : Path.Combine(_root, baseDir);
        if (!Directory.Exists(searchRoot))
        {
            yield break;
        }

        var count = 0;
        foreach (var file in Directory.EnumerateFiles(searchRoot, "*", SearchOption.AllDirectories))
        {
            cancellationToken.ThrowIfCancellationRequested();

            var relativePath = Path.GetRelativePath(_root, file).Replace('\\', '/');
            if (!pattern.IsMatch(relativePath))
            {
                continue;
            }

            if (fileFilter is not null && fileFilter.Count > 0 && !MatchesFilter(relativePath, fileFilter))
            {
                continue;
            }

            yield return new PipelineStorageItem(relativePath, new Dictionary<string, object?>(), File.GetCreationTimeUtc(file));

            if (maxCount.HasValue && ++count >= maxCount.Value)
            {
                break;
            }
        }

        await Task.CompletedTask;
    }

    public Task<Stream?> GetAsync(string key, bool asBytes = false, Encoding? encoding = null, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var fullPath = ResolvePath(key);
        if (!File.Exists(fullPath))
        {
            return Task.FromResult<Stream?>(null);
        }

        if (!asBytes && encoding is not null)
        {
            var text = File.ReadAllText(fullPath, encoding);
            return Task.FromResult<Stream?>(new MemoryStream(encoding.GetBytes(text)));
        }

        Stream stream = File.OpenRead(fullPath);
        return Task.FromResult<Stream?>(stream);
    }

    public async Task SetAsync(string key, Stream content, Encoding? encoding = null, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        ArgumentNullException.ThrowIfNull(content);

        var fullPath = ResolvePath(key);
        Directory.CreateDirectory(Path.GetDirectoryName(fullPath)!);

        await using var fileStream = File.Create(fullPath);
        await content.CopyToAsync(fileStream, cancellationToken).ConfigureAwait(false);
    }

    public Task<bool> HasAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(File.Exists(ResolvePath(key)));
    }

    public Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var fullPath = ResolvePath(key);
        if (File.Exists(fullPath))
        {
            File.Delete(fullPath);
        }

        return Task.CompletedTask;
    }

    public Task ClearAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (Directory.Exists(_root))
        {
            foreach (var file in Directory.EnumerateFiles(_root, "*", SearchOption.AllDirectories))
            {
                File.Delete(file);
            }
        }

        return Task.CompletedTask;
    }

    public IPipelineStorage CreateChild(string? name)
    {
        name ??= string.Empty;
        return new FilePipelineStorage(_root, name);
    }

    public IReadOnlyList<string> Keys
        => Directory.Exists(_root)
            ? Directory.EnumerateFiles(_root, "*", SearchOption.AllDirectories)
                .Select(path => Path.GetRelativePath(_root, path).Replace('\\', '/'))
                .ToArray()
            : Array.Empty<string>();

    public Task<DateTimeOffset?> GetCreationDateAsync(string key, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var fullPath = ResolvePath(key);
        return Task.FromResult(File.Exists(fullPath)
            ? new DateTimeOffset?(File.GetCreationTimeUtc(fullPath))
            : null);
    }

    private string ResolvePath(string key)
    {
        var path = key.Replace('/', Path.DirectorySeparatorChar);
        return Path.GetFullPath(Path.Combine(_root, path));
    }

    private static bool MatchesFilter(string path, IReadOnlyDictionary<string, object?> filter)
    {
        foreach (var kvp in filter)
        {
            if (!path.Contains(kvp.Value?.ToString() ?? string.Empty, StringComparison.OrdinalIgnoreCase))
            {
                return false;
            }
        }

        return true;
    }
}
