using GraphRag.Config;

namespace GraphRag.Chunking;

internal sealed class ChunkerResolver(TokenTextChunker tokenChunker, MarkdownTextChunker markdownChunker) : IChunkerResolver
{
    public ITextChunker Resolve(ChunkStrategyType strategy)
    {
        return strategy switch
        {
            ChunkStrategyType.Tokens => tokenChunker,
            ChunkStrategyType.Sentence => markdownChunker,
            _ => tokenChunker
        };
    }
}
