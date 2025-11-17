namespace GraphRag.Config;

public sealed class LocalSearchConfig
{
    public string? Prompt { get; set; }

    public string ChatModelId { get; set; } = "default_chat_model";

    public string EmbeddingModelId { get; set; } = "default_embedding_model";

    public double TextUnitProportion { get; set; } = 0.5;

    public double CommunityProportion { get; set; } = 0.15;

    public int ConversationHistoryMaxTurns { get; set; } = 5;

    public int TopKEntities { get; set; } = 10;

    public int TopKRelationships { get; set; } = 10;

    public int MaxContextTokens { get; set; } = 12_000;
}
