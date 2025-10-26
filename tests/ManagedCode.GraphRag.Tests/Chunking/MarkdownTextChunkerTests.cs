using System.Linq;
using GraphRag.Chunking;
using GraphRag.Config;
using GraphRag.Tokenization;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Chunking;

public sealed class MarkdownTextChunkerTests
{
    private static readonly TiktokenTokenizerProvider Provider = new();
    private readonly MarkdownTextChunker _chunker = new(Provider);

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
            EncodingModel = "o200k_base"
        };

        var chunks = _chunker.Chunk(slices, config);

        Assert.NotEmpty(chunks);
        Assert.All(chunks, chunk => Assert.Contains("doc-1", chunk.DocumentIds));
        Assert.True(chunks.Count >= 2);
        Assert.All(chunks, chunk => Assert.True(chunk.TokenCount > 0));
    }
}
