using BenchmarkDotNet.Attributes;
using GraphRag.Chunking;
using GraphRag.Config;

namespace ManagedCode.GraphRag.Benchmarks.Chunking;

[MemoryDiagnoser]
public class TokenTextChunkerBenchmarks
{
    private TokenTextChunker _chunker = null!;
    private ChunkSlice[] _smallDocument = null!;
    private ChunkSlice[] _mediumDocument = null!;
    private ChunkSlice[] _largeDocument = null!;
    private ChunkingConfig _config = null!;

    [Params(512, 1024, 2048)]
    public int ChunkSize { get; set; }

    [Params(0, 64, 128)]
    public int ChunkOverlap { get; set; }

    [GlobalSetup]
    public void Setup()
    {
        _chunker = new TokenTextChunker();
        _config = new ChunkingConfig
        {
            Size = ChunkSize,
            Overlap = ChunkOverlap,
            Strategy = ChunkStrategyType.Tokens
        };

        // Generate plain text documents of different sizes
        _smallDocument = new[] { new ChunkSlice("doc1", GeneratePlainTextDocument(1_000)) };
        _mediumDocument = new[] { new ChunkSlice("doc1", GeneratePlainTextDocument(100_000)) };
        _largeDocument = new[] { new ChunkSlice("doc1", GeneratePlainTextDocument(1_000_000)) };
    }

    [Benchmark]
    public IReadOnlyList<TextChunk> ChunkSmallDocument()
    {
        return _chunker.Chunk(_smallDocument, _config);
    }

    [Benchmark]
    public IReadOnlyList<TextChunk> ChunkMediumDocument()
    {
        return _chunker.Chunk(_mediumDocument, _config);
    }

    [Benchmark]
    public IReadOnlyList<TextChunk> ChunkLargeDocument()
    {
        return _chunker.Chunk(_largeDocument, _config);
    }

    private static string GeneratePlainTextDocument(int approximateLength)
    {
        var sentences = new[]
        {
            "The quick brown fox jumps over the lazy dog. ",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. ",
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ",
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris. ",
            "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore. ",
            "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia. ",
            "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit. ",
            "Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet. "
        };

        var result = new System.Text.StringBuilder(approximateLength + 200);
        var index = 0;

        while (result.Length < approximateLength)
        {
            result.Append(sentences[index % sentences.Length]);
            index++;
        }

        return result.ToString();
    }
}
