using System.Collections.Concurrent;
using GraphRag.Config;

namespace GraphRag.LanguageModels;

internal sealed class PromptTemplateLoader
{
    private readonly GraphRagConfig _config;
    private readonly ConcurrentDictionary<string, string?> _cache = new(StringComparer.OrdinalIgnoreCase);

    private PromptTemplateLoader(GraphRagConfig config)
    {
        _config = config;
    }

    public static PromptTemplateLoader Create(GraphRagConfig config)
    {
        ArgumentNullException.ThrowIfNull(config);
        return new PromptTemplateLoader(config);
    }

    public string ResolveOrDefault(string stageKey, string? explicitPath, string defaultValue)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(stageKey);
        ArgumentNullException.ThrowIfNull(defaultValue);

        var resolved = ResolveInternal(stageKey, explicitPath);
        return string.IsNullOrWhiteSpace(resolved) ? defaultValue : resolved!;
    }

    public string? ResolveOptional(string stageKey, string? explicitPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(stageKey);
        return ResolveInternal(stageKey, explicitPath);
    }

    private string? ResolveInternal(string stageKey, string? explicitPath)
    {
        var cacheKey = $"{stageKey}::{explicitPath}";
        if (_cache.TryGetValue(cacheKey, out var cached))
        {
            return cached;
        }

        var result = LoadPrompt(stageKey, explicitPath);
        _cache[cacheKey] = result;
        return result;
    }

    private string? LoadPrompt(string stageKey, string? explicitPath)
    {
        if (TryReadFile(explicitPath, out var value))
        {
            return value;
        }

        if (TryReadFromDirectory(_config.PromptTuning?.Manual, stageKey, out value))
        {
            return value;
        }

        if (TryReadFromDirectory(_config.PromptTuning?.Auto, stageKey, out value))
        {
            return value;
        }

        if (!string.IsNullOrWhiteSpace(explicitPath))
        {
            var inline = ExtractInlinePrompt(explicitPath);
            if (!string.IsNullOrWhiteSpace(inline))
            {
                return inline;
            }
        }

        return null;
    }

    private bool TryReadFromDirectory(ManualPromptTuningConfig? tuning, string stageKey, out string? value)
    {
        value = null;
        if (tuning is null || !tuning.Enabled || string.IsNullOrWhiteSpace(tuning.Directory))
        {
            return false;
        }

        var directory = ResolveDirectory(tuning.Directory!);
        var candidate = BuildPath(directory, stageKey);
        return TryReadFile(candidate, out value);
    }

    private bool TryReadFromDirectory(AutoPromptTuningConfig? tuning, string stageKey, out string? value)
    {
        value = null;
        if (tuning is null || !tuning.Enabled || string.IsNullOrWhiteSpace(tuning.Directory))
        {
            return false;
        }

        var directory = ResolveDirectory(tuning.Directory!);
        var candidate = BuildPath(directory, stageKey);
        return TryReadFile(candidate, out value);
    }

    private bool TryReadFile(string? path, out string? value)
    {
        value = null;
        if (string.IsNullOrWhiteSpace(path))
        {
            return false;
        }

        var resolved = ResolvePath(path);
        if (!File.Exists(resolved))
        {
            return false;
        }

        value = File.ReadAllText(resolved);
        return true;
    }

    private string ResolveDirectory(string directory)
    {
        if (Path.IsPathRooted(directory))
        {
            return Path.GetFullPath(directory);
        }

        var root = string.IsNullOrWhiteSpace(_config.RootDir)
            ? Directory.GetCurrentDirectory()
            : _config.RootDir;

        return Path.GetFullPath(Path.Combine(root, directory));
    }

    private string ResolvePath(string path)
    {
        if (Path.IsPathRooted(path))
        {
            return Path.GetFullPath(path);
        }

        var root = string.IsNullOrWhiteSpace(_config.RootDir)
            ? Directory.GetCurrentDirectory()
            : _config.RootDir;

        return Path.GetFullPath(Path.Combine(root, path));
    }

    private static string BuildPath(string directory, string stageKey)
    {
        var relative = stageKey.Replace('/', Path.DirectorySeparatorChar);
        var candidate = Path.Combine(directory, relative);
        return Path.HasExtension(candidate) ? candidate : candidate + ".txt";
    }

    private static readonly char[] InlineSeparators = new[] { '\r', '\n' };

    private static string? ExtractInlinePrompt(string candidate)
    {
        if (candidate.StartsWith("inline:", StringComparison.OrdinalIgnoreCase))
        {
            return candidate[7..].TrimStart();
        }

        return candidate.IndexOfAny(InlineSeparators) >= 0
            ? candidate
            : null;
    }
}
