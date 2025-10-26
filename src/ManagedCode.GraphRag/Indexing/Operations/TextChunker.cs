using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using GraphRag.Config;
using GraphRag.Data;

namespace GraphRag.Indexing.Operations;

internal static class TextChunker
{
    public static IReadOnlyList<ChunkResult> Chunk(DocumentRecord document, ChunkingConfig config, string? metadataPrefix = null, bool chunkSizeIncludesMetadata = false)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(config);

        var tokens = TextTokenizer.Tokenize(document.Text);
        if (tokens.Count == 0)
        {
            return Array.Empty<ChunkResult>();
        }

        var metadataTokens = metadataPrefix is not null ? TextTokenizer.Tokenize(metadataPrefix) : Array.Empty<TextTokenizer.Token>();
        var metadataTokenCount = metadataTokens.Count(token => token.CountsTowardsLimit);

        var tokenLimit = config.Size;
        if (chunkSizeIncludesMetadata)
        {
            if (metadataTokenCount >= tokenLimit)
            {
                throw new InvalidOperationException("Metadata token length exceeds configured chunk size. Increase chunk size or disable metadata prepending.");
            }

            tokenLimit -= metadataTokenCount;
        }

        var overlap = Math.Max(0, config.Overlap);
        var step = Math.Max(1, tokenLimit - overlap);

        var results = new List<ChunkResult>();
        var index = 0;

        while (index < tokens.Count)
        {
            var builder = new StringBuilder();
            var countedTokens = 0;
            var endIndex = index;

            if (metadataPrefix is not null)
            {
                builder.Append(metadataPrefix);
                if (!metadataPrefix.EndsWith(".\n", StringComparison.Ordinal))
                {
                    builder.Append(".\n");
                }
            }

            while (endIndex < tokens.Count && countedTokens < tokenLimit)
            {
                var token = tokens[endIndex];
                builder.Append(token.Value);
                if (token.CountsTowardsLimit)
                {
                    countedTokens++;
                }

                endIndex++;
            }

            if (countedTokens == 0)
            {
                break;
            }

            var chunkText = builder.ToString().Trim();
            if (!string.IsNullOrEmpty(chunkText))
            {
                results.Add(new ChunkResult(new[] { document.Id }, chunkText, countedTokens));
            }

            if (endIndex >= tokens.Count)
            {
                break;
            }

            var rewind = overlap;
            var rewindIndex = endIndex;
            while (rewind > 0 && rewindIndex > 0)
            {
                rewindIndex--;
                if (tokens[rewindIndex].CountsTowardsLimit)
                {
                    rewind--;
                }
            }

            index = rewindIndex;
        }

        return results;
    }

    internal sealed record ChunkResult(IReadOnlyList<string> DocumentIds, string Text, int TokenCount);
}
