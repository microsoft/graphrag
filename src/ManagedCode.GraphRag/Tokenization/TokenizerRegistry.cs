using System.Collections.Concurrent;
using GraphRag.Constants;
using Microsoft.ML.Tokenizers;

namespace GraphRag.Tokenization;

public static class TokenizerRegistry
{
    private static readonly ConcurrentDictionary<string, Tokenizer> Cache = new(StringComparer.OrdinalIgnoreCase);

    public static Tokenizer GetTokenizer() => GetTokenizer(TokenizerDefaults.DefaultEncoding);

    public static Tokenizer GetTokenizer(string? encodingOrModel)
    {
        var key = string.IsNullOrWhiteSpace(encodingOrModel)
            ? TokenizerDefaults.DefaultEncoding
            : encodingOrModel;
        return Cache.GetOrAdd(key, ResolveTokenizer);
    }

    private static Tokenizer ResolveTokenizer(string key)
    {
        if (TryCreate(() => TiktokenTokenizer.CreateForEncoding(key), out var encodingTokenizer))
        {
            return encodingTokenizer!;
        }

        if (TryCreate(() => TiktokenTokenizer.CreateForModel(key), out var modelTokenizer))
        {
            return modelTokenizer!;
        }

        foreach (var model in TokenizerDefaults.PreferredModels)
        {
            if (TryCreate(() => TiktokenTokenizer.CreateForModel(model), out var fallbackModel))
            {
                return fallbackModel!;
            }
        }

        foreach (var encoding in TokenizerDefaults.PreferredEncodings)
        {
            if (TryCreate(() => TiktokenTokenizer.CreateForEncoding(encoding), out var fallbackEncoding))
            {
                return fallbackEncoding!;
            }
        }

        if (TryCreate(() => TiktokenTokenizer.CreateForModel(TokenizerDefaults.DefaultModel), out var defaultModel))
        {
            return defaultModel!;
        }

        throw new NotSupportedException($"Unsupported encoding or model '{key}'.");
    }

    private static bool TryCreate(Func<Tokenizer> factory, out Tokenizer? tokenizer)
    {
        try
        {
            tokenizer = factory();
            return true;
        }
        catch
        {
            tokenizer = null;
            return false;
        }
    }
}
