using System.Collections.Generic;
using System.Linq;
using GraphRag.Config;
using GraphRag.Tokenization;

namespace GraphRag.Chunking;

public sealed class TokenTextChunker : ITextChunker
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
        var flattened = new List<(int SliceIndex, int Token)>();
        for (var index = 0; index < slices.Count; index++)
        {
            var slice = slices[index];
            var encoded = tokenizer.EncodeToIds(slice.Text);
            foreach (var token in encoded)
            {
                flattened.Add((index, token));
            }
        }

        if (flattened.Count == 0)
        {
            return Array.Empty<TextChunk>();
        }

        var chunkSize = Math.Max(1, config.Size);
        var overlap = Math.Clamp(config.Overlap, 0, chunkSize - 1);
        var results = new List<TextChunk>();

        var start = 0;
        while (start < flattened.Count)
        {
            var end = Math.Min(flattened.Count, start + chunkSize);
            var chunkTokens = flattened.GetRange(start, end - start);
            var tokenValues = new int[chunkTokens.Count];
            for (var i = 0; i < chunkTokens.Count; i++)
            {
                tokenValues[i] = chunkTokens[i].Token;
            }

            var decoded = tokenizer.Decode(tokenValues);
            var documentIds = chunkTokens
                .Select(tuple => slices[tuple.SliceIndex].DocumentId)
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToArray();

            results.Add(new TextChunk(documentIds, decoded, tokenValues.Length));

            if (end >= flattened.Count)
            {
                break;
            }

            start = Math.Max(start + chunkSize - overlap, start + 1);
        }

        return results;
    }
}
