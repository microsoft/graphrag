using BenchmarkDotNet.Attributes;
using GraphRag.Chunking;
using GraphRag.Config;

namespace ManagedCode.GraphRag.Benchmarks.Chunking;

[MemoryDiagnoser]
public class MarkdownTextChunkerBenchmarks
{
    private MarkdownTextChunker _chunker = null!;
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
        _chunker = new MarkdownTextChunker();
        _config = new ChunkingConfig
        {
            Size = ChunkSize,
            Overlap = ChunkOverlap,
            Strategy = ChunkStrategyType.Sentence
        };

        // Generate test documents of different sizes
        _smallDocument = new[] { new ChunkSlice("doc1", GenerateMarkdownDocument(1_000)) };
        _mediumDocument = new[] { new ChunkSlice("doc1", GenerateMarkdownDocument(100_000)) };
        _largeDocument = new[] { new ChunkSlice("doc1", GenerateMarkdownDocument(1_000_000)) };
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

    private static string GenerateMarkdownDocument(int approximateLength)
    {
        var paragraphs = new[]
        {
            "# Introduction\n\nThis is a sample markdown document for benchmarking purposes. It contains various markdown elements including headers, paragraphs, lists, and code blocks.\n\n",
            "## Section One\n\nLorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.\n\n",
            "### Subsection A\n\nDuis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.\n\n",
            "- First item in the list\n- Second item with more content\n- Third item explaining something important\n\n",
            "1. Numbered first item\n2. Numbered second item\n3. Numbered third item with explanation\n\n",
            "```csharp\npublic class Example\n{\n    public void Method() { }\n}\n```\n\n",
            "## Section Two\n\nSunt in culpa qui officia deserunt mollit anim id est laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.\n\n",
            "> This is a blockquote that spans multiple lines and contains important information that should be preserved during chunking.\n\n",
            "### Subsection B\n\nNemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.\n\n",
            "| Column 1 | Column 2 | Column 3 |\n|----------|----------|----------|\n| Data 1   | Data 2   | Data 3   |\n| Data 4   | Data 5   | Data 6   |\n\n"
        };

        var result = new System.Text.StringBuilder(approximateLength + 1000);
        var index = 0;

        while (result.Length < approximateLength)
        {
            result.Append(paragraphs[index % paragraphs.Length]);
            index++;
        }

        return result.ToString();
    }
}
