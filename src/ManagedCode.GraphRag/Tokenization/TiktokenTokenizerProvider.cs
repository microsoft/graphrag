using System;
using System.Collections.Concurrent;
using Microsoft.ML.Tokenizers;

namespace GraphRag.Tokenization;

public sealed class TiktokenTokenizerProvider : ITokenizerProvider
{
    private static readonly string DefaultEncoding = "o200k_base";
    private readonly ConcurrentDictionary<string, ITextTokenizer> _cache = new(StringComparer.OrdinalIgnoreCase);

    public ITextTokenizer GetTokenizer(string encodingName)
    {
        var key = string.IsNullOrWhiteSpace(encodingName) ? DefaultEncoding : encodingName;
        return _cache.GetOrAdd(key, CreateTokenizer);
    }

    private static ITextTokenizer CreateTokenizer(string encodingName)
    {
        // Prefer the explicit encoding if available; otherwise fall back to a known GPT-4 family model.
        if (TryCreate(() => TiktokenTokenizer.CreateForEncoding(encodingName), out var encodingTokenizer))
        {
            return new TiktokenAdapter(encodingTokenizer!);
        }

        if (TryCreate(() => TiktokenTokenizer.CreateForModel(encodingName), out var modelTokenizer))
        {
            return new TiktokenAdapter(modelTokenizer!);
        }

        var fallback = TiktokenTokenizer.CreateForModel("gpt-4o");
        return new TiktokenAdapter(fallback);
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

    private sealed class TiktokenAdapter : ITextTokenizer
    {
        private readonly Tokenizer _tokenizer;

        public TiktokenAdapter(Tokenizer tokenizer)
        {
            _tokenizer = tokenizer;
        }

        public int CountTokens(string text)
        {
            if (string.IsNullOrEmpty(text))
            {
                return 0;
            }

            return Encode(text).Count;
        }

        public IReadOnlyList<int> Encode(string text)
        {
            return _tokenizer.EncodeToIds(text);
        }

        public string Decode(IReadOnlyList<int> tokens)
        {
            return _tokenizer.Decode(tokens);
        }
    }
}
