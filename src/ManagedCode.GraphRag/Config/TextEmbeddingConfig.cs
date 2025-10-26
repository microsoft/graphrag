using System.Collections.Generic;

namespace GraphRag.Config;

public sealed class TextEmbeddingConfig
{
    public string ModelId { get; set; } = "default_embedding_model";

    public string VectorStoreId { get; set; } = "default_vector_store";

    public int BatchSize { get; set; } = 16;

    public int BatchMaxTokens { get; set; } = 8191;

    public List<string> Names { get; set; } = new();

    public Dictionary<string, object?>? Strategy { get; set; }
        = new();
}
