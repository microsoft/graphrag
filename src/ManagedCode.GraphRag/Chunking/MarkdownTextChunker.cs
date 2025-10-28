using System.Text;
using GraphRag.Config;
using GraphRag.Tokenization;
using Microsoft.ML.Tokenizers;

namespace GraphRag.Chunking;

public sealed class MarkdownTextChunker : ITextChunker
{
    public IReadOnlyList<TextChunk> Chunk(IReadOnlyList<ChunkSlice> slices, ChunkingConfig config)
    {
        ArgumentNullException.ThrowIfNull(slices);
        ArgumentNullException.ThrowIfNull(config);

        if (slices.Count == 0)
        {
            return Array.Empty<TextChunk>();
        }

        var tokenizer = TokenizerRegistry.GetTokenizer(config.EncodingModel);
        var options = new MarkdownChunkerOptions
        {
            MaxTokensPerChunk = Math.Max(MinChunkSize, config.Size),
            Overlap = Math.Max(0, config.Overlap)
        };

        var results = new List<TextChunk>();

        foreach (var slice in slices)
        {
            var fragments = Split(slice.Text, options, tokenizer);
            foreach (var fragment in fragments)
            {
                var tokens = tokenizer.EncodeToIds(fragment);
                if (tokens.Count == 0)
                {
                    continue;
                }

                results.Add(new TextChunk(new[] { slice.DocumentId }, fragment, tokens.Count));
            }
        }

        return results;
    }

    private List<string> Split(string text, MarkdownChunkerOptions options, Tokenizer tokenizer)
    {
        text = NormalizeNewlines(text);
        var firstChunkDone = false;
        var primarySize = options.MaxTokensPerChunk;
        var secondarySize = Math.Max(MinChunkSize, options.MaxTokensPerChunk - options.Overlap);

        var rawChunks = RecursiveSplit(text, primarySize, secondarySize, SeparatorType.ExplicitSeparator, tokenizer, ref firstChunkDone);

        if (options.Overlap > 0 && rawChunks.Count > 1)
        {
            var newChunks = new List<string> { rawChunks[0] };

            for (var index = 1; index < rawChunks.Count; index++)
            {
                var previousTokens = tokenizer.EncodeToIds(rawChunks[index - 1]);
                var overlapTokens = previousTokens.Skip(Math.Max(0, previousTokens.Count - options.Overlap)).ToArray();
                var overlapText = tokenizer.Decode(overlapTokens);
                newChunks.Add(string.Concat(overlapText, rawChunks[index]));
            }

            rawChunks = newChunks;
        }

        return MergeImageChunks(rawChunks);
    }

    private List<string> RecursiveSplit(
        string text,
        int maxChunk1Size,
        int maxChunkNSize,
        SeparatorType separatorType,
        Tokenizer tokenizer,
        ref bool firstChunkDone)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return [];
        }

        var maxChunkSize = firstChunkDone ? maxChunkNSize : maxChunk1Size;
        if (tokenizer.CountTokens(text) <= maxChunkSize)
        {
            return [text];
        }

        var fragments = separatorType switch
        {
            SeparatorType.ExplicitSeparator => SplitToFragments(text, ExplicitSeparators),
            SeparatorType.PotentialSeparator => SplitToFragments(text, PotentialSeparators),
            SeparatorType.WeakSeparator1 => SplitToFragments(text, WeakSeparators1),
            SeparatorType.WeakSeparator2 => SplitToFragments(text, WeakSeparators2),
            SeparatorType.WeakSeparator3 => SplitToFragments(text, WeakSeparators3),
            SeparatorType.NotASeparator => SplitToFragments(text, null),
            _ => throw new ArgumentOutOfRangeException(nameof(separatorType), separatorType, null)
        };

        return GenerateChunks(fragments, maxChunk1Size, maxChunkNSize, separatorType, tokenizer, ref firstChunkDone);
    }

    private List<string> GenerateChunks(
        List<Fragment> fragments,
        int maxChunk1Size,
        int maxChunkNSize,
        SeparatorType separatorType,
        Tokenizer tokenizer,
        ref bool firstChunkDone)
    {
        if (fragments.Count == 0)
        {
            return [];
        }

        var chunks = new List<string>();
        var builder = new ChunkBuilder();

        foreach (var fragment in fragments)
        {
            builder.NextSentence.Append(fragment.Content);

            if (!fragment.IsSeparator)
            {
                continue;
            }

            var nextSentence = builder.NextSentence.ToString();
            var nextSentenceSize = tokenizer.CountTokens(nextSentence);
            var maxChunkSize = firstChunkDone ? maxChunkNSize : maxChunk1Size;
            var chunkEmpty = builder.FullContent.Length == 0;
            var sentenceTooLong = nextSentenceSize > maxChunkSize;

            if (chunkEmpty && !sentenceTooLong)
            {
                builder.FullContent.Append(nextSentence);
                builder.NextSentence.Clear();
                continue;
            }

            if (chunkEmpty)
            {
                var moreChunks = RecursiveSplit(nextSentence, maxChunk1Size, maxChunkNSize, NextSeparatorType(separatorType), tokenizer, ref firstChunkDone);
                chunks.AddRange(moreChunks.Take(moreChunks.Count - 1));
                builder.NextSentence.Clear().Append(moreChunks.Last());
                continue;
            }

            var chunkPlusSentence = builder.FullContent.ToString() + builder.NextSentence;
            if (!sentenceTooLong && tokenizer.CountTokens(chunkPlusSentence) <= maxChunkSize)
            {
                builder.FullContent.Append(builder.NextSentence);
                builder.NextSentence.Clear();
                continue;
            }

            AddChunk(chunks, builder.FullContent, ref firstChunkDone);

            if (sentenceTooLong)
            {
                var moreChunks = RecursiveSplit(nextSentence, maxChunk1Size, maxChunkNSize, NextSeparatorType(separatorType), tokenizer, ref firstChunkDone);
                chunks.AddRange(moreChunks.Take(moreChunks.Count - 1));
                builder.NextSentence.Clear().Append(moreChunks.Last());
            }
            else
            {
                builder.FullContent.Clear().Append(builder.NextSentence);
                builder.NextSentence.Clear();
            }
        }

        var fullSentenceLeft = builder.FullContent.ToString();
        var nextSentenceLeft = builder.NextSentence.ToString();
        var remainingMax = firstChunkDone ? maxChunkNSize : maxChunk1Size;

        if (tokenizer.CountTokens(fullSentenceLeft + nextSentenceLeft) <= remainingMax)
        {
            if (fullSentenceLeft.Length > 0 || nextSentenceLeft.Length > 0)
            {
                AddChunk(chunks, fullSentenceLeft + nextSentenceLeft, ref firstChunkDone);
            }

            return chunks;
        }

        if (fullSentenceLeft.Length > 0)
        {
            AddChunk(chunks, fullSentenceLeft, ref firstChunkDone);
        }

        if (nextSentenceLeft.Length == 0)
        {
            return chunks;
        }

        if (tokenizer.CountTokens(nextSentenceLeft) <= remainingMax)
        {
            AddChunk(chunks, nextSentenceLeft, ref firstChunkDone);
        }
        else
        {
            var moreChunks = RecursiveSplit(nextSentenceLeft, maxChunk1Size, maxChunkNSize, NextSeparatorType(separatorType), tokenizer, ref firstChunkDone);
            chunks.AddRange(moreChunks);
        }

        return chunks;
    }

    private static List<Fragment> SplitToFragments(string text, SeparatorTrie? separators)
    {
        if (separators is null)
        {
            return text.Select(ch => new Fragment(ch.ToString(), true)).ToList();
        }

        if (text.Length == 0 || separators.Length == 0)
        {
            return [];
        }

        var fragments = new List<Fragment>();
        var fragmentBuilder = new StringBuilder();
        var index = 0;

        while (index < text.Length)
        {
            var found = separators.MatchLongest(text, index);

            if (found is not null)
            {
                if (fragmentBuilder.Length > 0)
                {
                    fragments.Add(new Fragment(fragmentBuilder.ToString(), false));
                    fragmentBuilder.Clear();
                }

                fragments.Add(new Fragment(found, true));
                index += found.Length;
            }
            else
            {
                fragmentBuilder.Append(text[index]);
                index++;
            }
        }

        if (fragmentBuilder.Length > 0)
        {
            fragments.Add(new Fragment(fragmentBuilder.ToString(), false));
        }

        return fragments;
    }

    private static List<string> MergeImageChunks(List<string> chunks)
    {
        if (chunks.Count <= 1)
        {
            return chunks;
        }

        var merged = new List<string>();

        foreach (var chunk in chunks)
        {
            var trimmed = chunk.TrimStart();
            if (trimmed.StartsWith("![", StringComparison.Ordinal) && merged.Count > 0)
            {
                merged[^1] = string.Concat(merged[^1].TrimEnd(), "\n\n", chunk.TrimStart());
            }
            else
            {
                merged.Add(chunk);
            }
        }

        return merged;
    }

    private static void AddChunk(List<string> chunks, StringBuilder builder, ref bool firstChunkDone)
    {
        var chunk = builder.ToString();
        if (!string.IsNullOrWhiteSpace(chunk))
        {
            chunks.Add(chunk);
            firstChunkDone = true;
        }

        builder.Clear();
    }

    private static void AddChunk(List<string> chunks, string chunk, ref bool firstChunkDone)
    {
        if (!string.IsNullOrWhiteSpace(chunk))
        {
            chunks.Add(chunk);
            firstChunkDone = true;
        }
    }

    private static SeparatorType NextSeparatorType(SeparatorType separatorType) => separatorType switch
    {
        SeparatorType.ExplicitSeparator => SeparatorType.PotentialSeparator,
        SeparatorType.PotentialSeparator => SeparatorType.WeakSeparator1,
        SeparatorType.WeakSeparator1 => SeparatorType.WeakSeparator2,
        SeparatorType.WeakSeparator2 => SeparatorType.WeakSeparator3,
        SeparatorType.WeakSeparator3 => SeparatorType.NotASeparator,
        _ => SeparatorType.NotASeparator
    };

    private static string NormalizeNewlines(string input) => input.Replace("\r\n", "\n", StringComparison.Ordinal).Replace('\r', '\n');

    private const int MinChunkSize = 5;

    private static readonly SeparatorTrie ExplicitSeparators = new([
        ".\n\n",
        "!\n\n",
        "!!\n\n",
        "!!!\n\n",
        "?\n\n",
        "??\n\n",
        "???\n\n",
        "\n\n",
        "\n#",
        "\n##",
        "\n###",
        "\n####",
        "\n#####",
        "\n---"
    ]);

    private static readonly SeparatorTrie PotentialSeparators = new([
        "\n> ",
        "\n>- ",
        "\n>* ",
        "\n1. ",
        "\n2. ",
        "\n3. ",
        "\n4. ",
        "\n5. ",
        "\n6. ",
        "\n7. ",
        "\n8. ",
        "\n9. ",
        "\n10. ",
        "\n```"
    ]);

    private static readonly SeparatorTrie WeakSeparators1 = new([
        "![",
        "[",
        "| ",
        " |\n",
        "-|\n",
        "\n: "
    ]);

    private static readonly SeparatorTrie WeakSeparators2 = new([
        ". ", ".\t", ".\n",
        "? ", "?\t", "?\n",
        "! ", "!\t", "!\n",
        "⁉ ", "⁉\t", "⁉\n",
        "⁈ ", "⁈\t", "⁈\n",
        "⁇ ", "⁇\t", "⁇\n",
        "… ", "…\t", "…\n",
        "!!!!", "????", "!!!", "???", "?!?", "!?!", "!?", "?!", "!!", "??", "....", "...", "..",
        ".", "?", "!", "⁉", "⁈", "⁇", "…"
    ]);

    private static readonly SeparatorTrie WeakSeparators3 = new([
        "; ", ";\t", ";\n", ";",
        "} ", "}\t", "}\n", "}",
        ") ", ")\t", ")\n",
        "] ", "]\t", "]\n",
        ")", "]",
        ": ", ":",
        ", ", ",",
        "\n"
    ]);

    private enum SeparatorType
    {
        ExplicitSeparator,
        PotentialSeparator,
        WeakSeparator1,
        WeakSeparator2,
        WeakSeparator3,
        NotASeparator
    }

    private sealed record Fragment(string Content, bool IsSeparator);

    private sealed class ChunkBuilder
    {
        public StringBuilder FullContent { get; } = new();
        public StringBuilder NextSentence { get; } = new();
    }

    private sealed class MarkdownChunkerOptions
    {
        public int MaxTokensPerChunk { get; init; }
        public int Overlap { get; init; }
    }

    private sealed class SeparatorTrie
    {
        private readonly Dictionary<char, List<string>> _lookup = new();

        public int Length { get; }

        public SeparatorTrie(IEnumerable<string> separators)
        {
            var list = separators.Where(static s => !string.IsNullOrEmpty(s)).ToList();
            Length = list.Count;

            foreach (var separator in list)
            {
                var key = separator[0];
                if (!_lookup.TryGetValue(key, out var bucket))
                {
                    bucket = [];
                    _lookup[key] = bucket;
                }

                bucket.Add(separator);
            }

            foreach (var bucket in _lookup.Values)
            {
                bucket.Sort((a, b) => b.Length.CompareTo(a.Length));
            }
        }

        public string? MatchLongest(string text, int index)
        {
            if (index >= text.Length)
            {
                return null;
            }

            if (!_lookup.TryGetValue(text[index], out var candidates))
            {
                return null;
            }

            foreach (var candidate in candidates)
            {
                if (index + candidate.Length > text.Length)
                {
                    continue;
                }

                if (text.AsSpan(index, candidate.Length).SequenceEqual(candidate))
                {
                    return candidate;
                }
            }

            return null;
        }
    }
}
