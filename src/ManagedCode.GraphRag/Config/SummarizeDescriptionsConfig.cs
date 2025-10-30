namespace GraphRag.Config;

public sealed class SummarizeDescriptionsConfig
{
    public string? ModelId { get; set; }

    public string? Prompt { get; set; }

    public string? RelationshipPrompt { get; set; }

    public int MaxLength { get; set; } = 400;

    public Dictionary<string, object?>? Strategy { get; set; }
        = new();
}
