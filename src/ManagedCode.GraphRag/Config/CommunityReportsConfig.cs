namespace GraphRag.Config;

public sealed class CommunityReportsConfig
{
    public string? ModelId { get; set; }

    public string? GraphPrompt { get; set; }

    public string? TextPrompt { get; set; }

    public int MaxLength { get; set; } = 2000;

    public int MaxInputLength { get; set; } = 8000;

    public Dictionary<string, object?>? Strategy { get; set; }
        = new();
}
