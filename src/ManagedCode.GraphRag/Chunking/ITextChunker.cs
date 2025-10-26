using System.Collections.Generic;
using GraphRag.Config;

namespace GraphRag.Chunking;

public interface ITextChunker
{
    IReadOnlyList<TextChunk> Chunk(IReadOnlyList<ChunkSlice> slices, ChunkingConfig config);
}
