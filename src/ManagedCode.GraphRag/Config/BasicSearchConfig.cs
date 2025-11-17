namespace GraphRag.Config;

public sealed class BasicSearchConfig
{
    public string? Prompt { get; set; }

    public string ChatModelId { get; set; } = "default_chat_model";

    public string EmbeddingModelId { get; set; } = "default_embedding_model";

    public int K { get; set; } = 10;

    public int MaxContextTokens { get; set; } = 12_000;
}
