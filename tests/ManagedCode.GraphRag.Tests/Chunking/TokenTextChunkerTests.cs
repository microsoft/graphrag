using System.Linq;
using GraphRag.Chunking;
using GraphRag.Config;
using GraphRag.Tokenization;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Chunking;

public sealed class TokenTextChunkerTests
{
    private readonly TokenTextChunker _chunker = new(new TiktokenTokenizerProvider());

    [Fact]
    public void Chunk_RespectsTokenBudget()
    {
        var tokenizer = new TiktokenTokenizerProvider().GetTokenizer("o200k_base");
        const string baseSentence = "Alice met Bob at the conference and shared insights.";
        var text = string.Join(' ', Enumerable.Repeat(baseSentence, 16));
        var slices = new[] { new ChunkSlice("doc-1", text) };

        var config = new ChunkingConfig
        {
            Size = 40,
            Overlap = 10,
            EncodingModel = "o200k_base"
        };

        var totalTokens = tokenizer.Encode(text).Count;
        var chunks = _chunker.Chunk(slices, config);

        Assert.NotEmpty(chunks);
        Assert.All(chunks, chunk =>
        {
            Assert.Contains("doc-1", chunk.DocumentIds);
            Assert.True(chunk.TokenCount <= config.Size);
            Assert.False(string.IsNullOrWhiteSpace(chunk.Text));
        });

        if (totalTokens > config.Size)
        {
            Assert.True(chunks.Count > 1, "Expected multiple chunks when total tokens exceed configured size.");
        }
    }
}
