namespace GraphRag.Config;

public sealed class ExtractGraphConfig
{
    public string? ModelId { get; set; }

    public string? SystemPrompt { get; set; }

    public string? Prompt { get; set; }

    public List<string> EntityTypes { get; set; } = new() { "person", "organization", "location" };

    public int MaxGleanings { get; set; } = 1;

    public Dictionary<string, object?>? Strategy { get; set; }
        = new();
}
