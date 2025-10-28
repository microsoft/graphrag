namespace GraphRag.Config;

public sealed class ExtractGraphConfig
{
    public string ModelId { get; set; } = "default_chat_model";

    public string? Prompt { get; set; }
        = "prompts/index/extract_graph.txt";

    public List<string> EntityTypes { get; set; } = new() { "person", "organization", "location" };

    public int MaxGleanings { get; set; } = 1;

    public Dictionary<string, object?>? Strategy { get; set; }
        = new();
}
