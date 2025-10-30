using GraphRag.Chunking;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Tokenization;

namespace ManagedCode.GraphRag.Tests.Chunking;

public sealed class MarkdownTextChunkerTests
{
    private readonly MarkdownTextChunker _chunker = new();

    [Fact]
    public void Chunk_SplitsMarkdownBlocks()
    {
        var text = "# Title\n\nAlice met Bob.\n\n![image](path)\n\n" +
                   string.Join(" ", Enumerable.Repeat("This is a longer paragraph that should be chunked based on token limits.", 4));
        var slices = new[] { new ChunkSlice("doc-1", text) };

        var config = new ChunkingConfig
        {
            Size = 60,
            Overlap = 10,
            EncodingModel = TokenizerDefaults.DefaultEncoding
        };

        var chunks = _chunker.Chunk(slices, config);

        Assert.NotEmpty(chunks);
        Assert.All(chunks, chunk => Assert.Contains("doc-1", chunk.DocumentIds));
        Assert.True(chunks.Count >= 2);
        Assert.All(chunks, chunk => Assert.True(chunk.TokenCount > 0));
    }

    [Fact]
    public void Chunk_MergesImageBlocksIntoPrecedingChunk()
    {
        var text = string.Join(' ', Enumerable.Repeat("This paragraph provides enough content for chunking.", 6)) +
                   "\n\n![diagram](diagram.png)\nImage description follows with more narrative text.";
        var slices = new[] { new ChunkSlice("doc-1", text) };

        var config = new ChunkingConfig
        {
            Size = 60,
            Overlap = 0,
            EncodingModel = TokenizerDefaults.DefaultModel
        };

        var chunks = _chunker.Chunk(slices, config);

        Assert.NotEmpty(chunks);
        Assert.Contains(chunks, chunk => chunk.Text.Contains("![diagram](diagram.png)", StringComparison.Ordinal));
        Assert.DoesNotContain(chunks, chunk => chunk.Text.TrimStart().StartsWith("![", StringComparison.Ordinal));
    }

    [Fact]
    public void Chunk_RespectsOverlapBetweenChunks()
    {
        var text = string.Join(' ', Enumerable.Repeat("Token overlap ensures continuity across generated segments.", 20));
        var slices = new[] { new ChunkSlice("doc-1", text) };

        var config = new ChunkingConfig
        {
            Size = 80,
            Overlap = 20,
            EncodingModel = "gpt-4"
        };

        var chunks = _chunker.Chunk(slices, config);

        Assert.True(chunks.Count > 1);

        var tokenizer = TokenizerRegistry.GetTokenizer(config.EncodingModel);
        var firstTokens = tokenizer.EncodeToIds(chunks[0].Text);

        _ = tokenizer.EncodeToIds(chunks[1].Text);
        var overlapTokens = firstTokens.Skip(Math.Max(0, firstTokens.Count - config.Overlap)).ToArray();
        Assert.True(overlapTokens.Length > 0);
        var overlapText = tokenizer.Decode(overlapTokens).TrimStart();
        var secondText = chunks[1].Text.TrimStart();
        Assert.StartsWith(overlapText, secondText, StringComparison.Ordinal);
    }
}
