namespace GraphRag.Config;

public sealed class ChunkingConfig
{
    public int Size { get; set; } = 1200;

    public int Overlap { get; set; } = 100;

    public List<string> GroupByColumns { get; set; } = new() { "id" };

    public ChunkStrategyType Strategy { get; set; } = ChunkStrategyType.Tokens;

    public string EncodingModel { get; set; } = GraphRag.Constants.TokenizerDefaults.DefaultEncoding;

    public bool PrependMetadata { get; set; }

    public bool ChunkSizeIncludesMetadata { get; set; }

}
