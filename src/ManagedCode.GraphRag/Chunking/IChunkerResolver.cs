using GraphRag.Config;

namespace GraphRag.Chunking;

public interface IChunkerResolver
{
    ITextChunker Resolve(ChunkStrategyType strategy);
}
