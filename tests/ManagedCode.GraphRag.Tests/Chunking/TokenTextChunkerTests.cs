using GraphRag.Chunking;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Tokenization;

namespace ManagedCode.GraphRag.Tests.Chunking;

public sealed class TokenTextChunkerTests
{
    private readonly TokenTextChunker _chunker = new();

    [Fact]
    public void Chunk_RespectsTokenBudget()
    {
        var tokenizer = TokenizerRegistry.GetTokenizer(TokenizerDefaults.DefaultEncoding);
        const string baseSentence = "Alice met Bob at the conference and shared insights.";
        var text = string.Join(' ', Enumerable.Repeat(baseSentence, 16));
        var slices = new[] { new ChunkSlice("doc-1", text) };

        var config = new ChunkingConfig
        {
            Size = 40,
            Overlap = 10,
            EncodingModel = TokenizerDefaults.DefaultEncoding
        };

        var totalTokens = tokenizer.EncodeToIds(text).Count;
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

    [Fact]
    public void Chunk_CombinesDocumentIdentifiersAcrossSlices()
    {
        var slices = new[]
        {
            new ChunkSlice("doc-1", string.Join(' ', Enumerable.Repeat("First slice carries shared content.", 4))),
            new ChunkSlice("doc-2", string.Join(' ', Enumerable.Repeat("Second slice enriches the narrative.", 4)))
        };

        var config = new ChunkingConfig
        {
            Size = 50,
            Overlap = 10,
            EncodingModel = TokenizerDefaults.DefaultModel
        };

        var chunks = _chunker.Chunk(slices, config);

        Assert.NotEmpty(chunks);
        Assert.Contains(chunks, chunk => chunk.DocumentIds.Contains("doc-1"));
        Assert.Contains(chunks, chunk => chunk.DocumentIds.Contains("doc-2"));
    }
}
