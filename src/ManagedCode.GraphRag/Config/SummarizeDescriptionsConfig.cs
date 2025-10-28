namespace GraphRag.Config;

public sealed class SummarizeDescriptionsConfig
{
    public string ModelId { get; set; } = "default_chat_model";

    public string? Prompt { get; set; } = "prompts/index/summarize_entities.txt";

    public string? RelationshipPrompt { get; set; } = "prompts/index/summarize_relationships.txt";

    public int MaxLength { get; set; } = 400;

    public Dictionary<string, object?>? Strategy { get; set; }
        = new();
}
