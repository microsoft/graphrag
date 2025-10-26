using System.Collections.Generic;

namespace GraphRag.Chunking;

public sealed record TextChunk(IReadOnlyList<string> DocumentIds, string Text, int TokenCount);
